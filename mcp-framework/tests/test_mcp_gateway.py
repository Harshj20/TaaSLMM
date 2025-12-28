"""Quick test of MCP Gateway."""

import asyncio
import httpx


async def test_mcp_gateway():
    """Test MCP Gateway endpoints."""
    print("="*60)
    print("Testing MCP Gateway")
    print("="*60)
    
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        # Test 1: Health check
        print("\n1. Health Check")print("-"*60)
        response = await client.get(f"{base_url}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Test 2: List tools
        print("\n2. List Tools")
        print("-"*60)
        response = await client.get(f"{base_url}/mcp/tools")
        data = response.json()
        print(f"Found {data['count']} tools:")
        for tool in data['tools']:
            print(f"  - {tool['name']} ({tool['category']}): {tool['description']}")
        
        # Test 3: Call a tool
        print("\n3. Call load_dataset Tool")
        print("-"*60)
        response = await client.post(
            f"{base_url}/mcp/call",
            json={
                "name": "load_dataset",
                "arguments": {
                    "dataset_path": "huggingface:squad"
                }
            }
        )
        result = response.json()
        print(f"Status: {result['status']}")
        print(f"Result: {result['result']}")
    
    print("\n" + "="*60)
    print("✓ MCP Gateway Tests Complete!")
    print("="*60)


if __name__ == "__main__":
    print("\nNOTE: Start the MCP server first with: uv run mcp-server\n")
    asyncio.run(test_mcp_gateway())
