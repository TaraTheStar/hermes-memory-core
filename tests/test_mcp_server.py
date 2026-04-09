import asyncio
import os
import sys
from unittest.mock import MagicMock, patch

# Mocking the MemoryEngine to avoid real DB/Chroma connections during the test
# and to ensure we are only testing the MCP wrapper logic.
class MockMemoryEngine:
    def query(self, query: str):
        return [{"text": "mock result for " + query, "structural_context": "mock context"}]
    
    def ingest_interaction(self, user_text: str, assistant_text: str):
        return True
    
    def ledger(self):
        return MagicMock()

# Mock the imports that would normally come from the library
sys.modules["application"] = MagicMock()
sys.modules["application.engine"] = MagicMock()
sys.modules["application.engine"].MemoryEngine = MockMemoryEngine

# Now import the server (it will use our mocked MemoryEngine)
from src.mcp_server import mcp, query_memory, ingest_interaction, add_project, add_milestone, get_knowledge_graph_insights

def test_mcp_server_startup():
    """Verify the server instance exists and can be inspected."""
    assert mcp is not None
    assert mcp.name == "Hermes Memory"

@pytest.mark.asyncio
async def test_query_memory_tool():
    """Test the query_memory tool logic."""
    result = await query_memory("test query")
    assert "mock result for test query" in result
    assert "mock context" in result

@pytest.mark.asyncio
async def test_ingest_interaction_tool():
    """Test the ingest_interaction tool logic."""
    result = await ingest_interaction("hello", "hi there")
    assert result == "Interaction successfully ingested and processed."

@pytest.mark.asyncio
async def test_add_project_tool():
    """Test the add_project tool logic."""
    # Note: in our mock, engine.ledger.add_project returns a MagicMock
    # We need to ensure the mock returns something that looks like an ID
    with patch("application.engine.MemoryEngine.ledger") as mock_ledger:
        mock_ledger.return_value.add_project.return_value = 123
        result = await add_project("Test Project", "http://test.com")
        assert "Project 'Test Project' added with ID: 123" in result

@pytest.mark.asyncio
async def test_get_insights_tool():
    """Test the get_knowledge_graph_insights tool logic."""
    # This test is tricky because of the internal import in the tool.
    # We'll mock the GraphAnalyzer.
    with patch("domain.core.analyzer.GraphAnalyzer") as MockAnalyzer:
        instance = MockAnalyzer.return_value
        instance.build_graph.return_value = None
        instance.get_centrality_metrics.return_value = {"node1": 0.5}
        instance.detect_communities.return_value = [[1, 2]]
        instance.get_bridge_nodes.return_value = ["node2"]
        
        result = await get_knowledge_graph_insights()
        assert "### Knowledge Graph Insights" in result
        assert "node1: 0.5000" in result
        assert "Community 1: 1, 2..." in result
