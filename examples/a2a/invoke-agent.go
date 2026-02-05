package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"time"
)

// GatewayClient represents a client for the AI Security Gateway A2A API
type GatewayClient struct {
	BaseURL string
	APIKey  string
	Client  *http.Client
}

// NewGatewayClient creates a new Gateway client
func NewGatewayClient(baseURL, apiKey string) *GatewayClient {
	return &GatewayClient{
		BaseURL: baseURL,
		APIKey:  apiKey,
		Client: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// InvokeAgentRequest represents the request body for agent invocation
type InvokeAgentRequest struct {
	Message struct {
		Role  string `json:"role"`
		Parts []struct {
			Kind string `json:"kind"`
			Text string `json:"text"`
		} `json:"parts"`
	} `json:"message"`
	Streaming bool `json:"streaming,omitempty"`
}

// InvokeAgentResponse represents the response from agent invocation
type InvokeAgentResponse struct {
	Success bool        `json:"success"`
	Data    interface{} `json:"data,omitempty"`
	Error   string      `json:"error,omitempty"`
}

// InvokeAgent invokes an A2A agent via the Gateway
func (c *GatewayClient) InvokeAgent(ctx context.Context, agentID int, message string, streaming bool) error {
	// Build request
	reqBody := InvokeAgentRequest{
		Streaming: streaming,
	}
	reqBody.Message.Role = "user"
	reqBody.Message.Parts = []struct {
		Kind string `json:"kind"`
		Text string `json:"text"`
	}{
		{Kind: "text", Text: message},
	}

	jsonData, err := json.Marshal(reqBody)
	if err != nil {
		return fmt.Errorf("failed to marshal request: %w", err)
	}

	// Create HTTP request
	url := fmt.Sprintf("%s/api/v1/agents/%d/invoke", c.BaseURL, agentID)
	req, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewBuffer(jsonData))
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-API-Key", c.APIKey)

	// Handle streaming vs non-streaming
	if streaming {
		req.Header.Set("Accept", "text/event-stream")
		return c.handleStreamingResponse(ctx, req)
	}

	return c.handleNonStreamingResponse(ctx, req)
}

// handleNonStreamingResponse handles a non-streaming response
func (c *GatewayClient) handleNonStreamingResponse(ctx context.Context, req *http.Request) error {
	resp, err := c.Client.Do(req)
	if err != nil {
		return fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return fmt.Errorf("failed to read response: %w", err)
	}

	// Check for rate limit errors
	if resp.StatusCode == http.StatusTooManyRequests {
		var errorResp InvokeAgentResponse
		if err := json.Unmarshal(body, &errorResp); err == nil {
			return fmt.Errorf("rate limit exceeded: %s", errorResp.Error)
		}
		return fmt.Errorf("rate limit exceeded (HTTP %d)", resp.StatusCode)
	}

	// Check for other errors
	if resp.StatusCode != http.StatusOK {
		var errorResp InvokeAgentResponse
		if err := json.Unmarshal(body, &errorResp); err == nil {
			return fmt.Errorf("invocation failed: %s (code: %s)", errorResp.Error, errorResp.Error)
		}
		return fmt.Errorf("invocation failed with status %d: %s", resp.StatusCode, string(body))
	}

	// Parse successful response
	var response InvokeAgentResponse
	if err := json.Unmarshal(body, &response); err != nil {
		return fmt.Errorf("failed to parse response: %w", err)
	}

	if !response.Success {
		return fmt.Errorf("invocation failed: %s", response.Error)
	}

	// Pretty print response
	prettyJSON, err := json.MarshalIndent(response.Data, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to format response: %w", err)
	}

	fmt.Println("Agent Response:")
	fmt.Println(string(prettyJSON))
	return nil
}

// handleStreamingResponse handles a streaming response (SSE)
func (c *GatewayClient) handleStreamingResponse(ctx context.Context, req *http.Request) error {
	resp, err := c.Client.Do(req)
	if err != nil {
		return fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("streaming failed with status %d: %s", resp.StatusCode, string(body))
	}

	fmt.Println("Streaming Response (SSE):")
	fmt.Println("---")

	// Read SSE stream
	buf := make([]byte, 4096)
	var eventBuffer []byte

	for {
		select {
		case <-ctx.Done():
			return ctx.Err()
		default:
			n, err := resp.Body.Read(buf)
			if err != nil && err != io.EOF {
				return fmt.Errorf("failed to read stream: %w", err)
			}
			if n == 0 {
				if err == io.EOF {
					return nil
				}
				continue
			}

			eventBuffer = append(eventBuffer, buf[:n]...)

			// Process complete events (lines ending with \n\n)
			for {
				idx := bytes.Index(eventBuffer, []byte("\n\n"))
				if idx == -1 {
					break
				}

				event := string(eventBuffer[:idx])
				eventBuffer = eventBuffer[idx+2:]

				// Parse SSE event
				if bytes.HasPrefix([]byte(event), []byte("data: ")) {
					data := event[6:] // Skip "data: "
					fmt.Println(data)
				} else if bytes.HasPrefix([]byte(event), []byte("event: ")) {
					eventType := event[7:] // Skip "event: "
					fmt.Printf("[Event: %s]\n", eventType)
				}
			}
		}
	}
}

// ListAgents lists all accessible agents
func (c *GatewayClient) ListAgents(ctx context.Context) error {
	url := fmt.Sprintf("%s/api/v1/agents", c.BaseURL)
	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("X-API-Key", c.APIKey)

	resp, err := c.Client.Do(req)
	if err != nil {
		return fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("list failed with status %d: %s", resp.StatusCode, string(body))
	}

	var response struct {
		Success bool `json:"success"`
		Data    struct {
			Agents []struct {
				ID     int    `json:"id"`
				Name   string `json:"name"`
				Status string `json:"status"`
			} `json:"agents"`
		} `json:"data"`
	}

	if err := json.Unmarshal(body, &response); err != nil {
		return fmt.Errorf("failed to parse response: %w", err)
	}

	fmt.Println("Available Agents:")
	fmt.Println("---")
	for _, agent := range response.Data.Agents {
		fmt.Printf("ID: %d | Name: %s | Status: %s\n", agent.ID, agent.Name, agent.Status)
	}

	return nil
}

func main() {
	if len(os.Args) < 2 {
		fmt.Println("Usage: invoke-agent <command> [args...]")
		fmt.Println("")
		fmt.Println("Commands:")
		fmt.Println("  list <api-key>                    List available agents")
		fmt.Println("  invoke <api-key> <agent-id> <msg> Invoke agent (non-streaming)")
		fmt.Println("  stream <api-key> <agent-id> <msg> Invoke agent (streaming)")
		fmt.Println("")
		fmt.Println("Environment Variables:")
		fmt.Println("  GATEWAY_URL  Gateway URL (default: http://localhost:8080)")
		fmt.Println("")
		fmt.Println("Examples:")
		fmt.Println("  invoke-agent list YOUR_API_KEY")
		fmt.Println("  invoke-agent invoke YOUR_API_KEY 1 'Hello, agent!'")
		fmt.Println("  invoke-agent stream YOUR_API_KEY 1 'Calculate 2+2'")
		os.Exit(1)
	}

	gatewayURL := os.Getenv("GATEWAY_URL")
	if gatewayURL == "" {
		gatewayURL = "http://localhost:8080"
	}

	command := os.Args[1]

	ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
	defer cancel()

	client := NewGatewayClient(gatewayURL, "")

	switch command {
	case "list":
		if len(os.Args) < 3 {
			fmt.Println("Error: API key required")
			os.Exit(1)
		}
		client.APIKey = os.Args[2]
		if err := client.ListAgents(ctx); err != nil {
			fmt.Fprintf(os.Stderr, "Error: %v\n", err)
			os.Exit(1)
		}

	case "invoke":
		if len(os.Args) < 5 {
			fmt.Println("Error: API key, agent ID, and message required")
			os.Exit(1)
		}
		client.APIKey = os.Args[2]
		agentID := 0
		if _, err := fmt.Sscanf(os.Args[3], "%d", &agentID); err != nil {
			fmt.Printf("Error: Invalid agent ID: %s\n", os.Args[3])
			os.Exit(1)
		}
		message := os.Args[4]
		if err := client.InvokeAgent(ctx, agentID, message, false); err != nil {
			fmt.Fprintf(os.Stderr, "Error: %v\n", err)
			os.Exit(1)
		}

	case "stream":
		if len(os.Args) < 5 {
			fmt.Println("Error: API key, agent ID, and message required")
			os.Exit(1)
		}
		client.APIKey = os.Args[2]
		agentID := 0
		if _, err := fmt.Sscanf(os.Args[3], "%d", &agentID); err != nil {
			fmt.Printf("Error: Invalid agent ID: %s\n", os.Args[3])
			os.Exit(1)
		}
		message := os.Args[4]
		if err := client.InvokeAgent(ctx, agentID, message, true); err != nil {
			fmt.Fprintf(os.Stderr, "Error: %v\n", err)
			os.Exit(1)
		}

	default:
		fmt.Printf("Error: Unknown command: %s\n", command)
		os.Exit(1)
	}
}

