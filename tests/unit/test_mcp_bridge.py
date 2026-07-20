"""tests/unit/test_mcp_bridge.py
Unit tests for MCP Bridge sandboxing and file operations.
"""
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch


from core.mcp_bridge import MCPBridge, mcp_bridge, _is_allowed

class TestMCPSandbox:
    """Test MCP file operation sandboxing."""
    
    def test_path_allowed_in_home(self):
        """Paths within home should be allowed."""
        home = Path.home()
        test_file = home / "test.txt"
        with patch("core.mcp_bridge.ALLOWED_ROOTS", [home]):
            assert _is_allowed(test_file) is True
    
    def test_path_blocked_outside_home(self):
        """Paths outside home should be blocked."""
        blocked = Path("/etc/passwd")
        with patch("core.mcp_bridge.ALLOWED_ROOTS", [Path.home()]):
            assert _is_allowed(blocked) is False
    
    def test_path_blocked_system_critical(self):
        """System critical paths should be blocked."""
        assert _is_allowed(Path("/etc/")) is False
        assert _is_allowed(Path("/usr/bin")) is False
        assert _is_allowed(Path("/boot")) is False
    
    def test_symlink_traversal_blocked(self, tmp_path):
        """Symlink traversal should be detected and blocked."""
        # Create a symlink pointing outside allowed root
        safe_dir = tmp_path / "safe"
        safe_dir.mkdir()
        outside = tmp_path / "outside" / "secret.txt"
        outside.parent.mkdir(parents=True)
        outside.write_text("secret")
        
        symlink = safe_dir / "link"
        try:
            symlink.symlink_to(outside)
            # The bridge should resolve the real path and block it
            with patch("core.mcp_bridge.ALLOWED_ROOTS", [safe_dir]):
                assert _is_allowed(symlink) is False
        except OSError:
            # Windows may require admin for symlinks, skip
            pytest.skip("Symlink creation not available")
    
    @pytest.mark.asyncio
    async def test_read_file_safe(self, tmp_path):
        """Reading a safe file should succeed."""
        # Ensure tmp_path is in allowed roots for testing, or patch ALLOWED_ROOTS
        with patch("core.mcp_bridge.ALLOWED_ROOTS", [tmp_path]):
            test_file = tmp_path / "test.txt"
            test_file.write_text("Hello Aiko")
            
            result = await mcp_bridge.read_file(str(test_file))
            assert "Hello Aiko" in result
    
    @pytest.mark.asyncio
    async def test_read_file_blocked(self):
        """Reading a blocked file should fail gracefully."""
        result = await mcp_bridge.read_file("/etc/passwd")
        assert "error" in result.lower() or "denied" in result.lower()
    
    @pytest.mark.asyncio
    async def test_write_file_safe(self, tmp_path):
        """Writing to a safe path should succeed."""
        with patch("core.mcp_bridge.ALLOWED_ROOTS", [tmp_path]):
            test_file = tmp_path / "output.txt"
            result = await mcp_bridge.write_file(str(test_file), "Test content")
            assert "success" in result.lower() or "written" in result.lower() or "ok" in result.lower()
            assert test_file.read_text() == "Test content"
    
    @pytest.mark.asyncio
    async def test_write_file_blocked_system(self):
        """Writing to system paths should be blocked."""
        result = await mcp_bridge.write_file("/etc/malicious.txt", "bad")
        assert "error" in result.lower() or "denied" in result.lower()
    
    @pytest.mark.asyncio
    async def test_delete_file_safe(self, tmp_path):
        """Deleting a safe file should succeed."""
        with patch("core.mcp_bridge.ALLOWED_ROOTS", [tmp_path]):
            test_file = tmp_path / "delete_me.txt"
            test_file.write_text("delete me")
            
            result = await mcp_bridge.delete_file(str(test_file))
            assert "success" in result.lower() or "deleted" in result.lower() or "ok" in result.lower()
            assert not test_file.exists()
    
    @pytest.mark.asyncio
    async def test_delete_file_blocked(self):
        """Deleting system files should be blocked."""
        result = await mcp_bridge.delete_file("/etc/passwd")
        assert "error" in result.lower() or "denied" in result.lower()
    
    @pytest.mark.asyncio
    async def test_list_dir_safe(self, tmp_path):
        """Listing a safe directory should succeed."""
        with patch("core.mcp_bridge.ALLOWED_ROOTS", [tmp_path]):
            (tmp_path / "file1.txt").write_text("1")
            (tmp_path / "file2.txt").write_text("2")
            
            result = await mcp_bridge.list_dir(str(tmp_path))
            assert "file1.txt" in result
            assert "file2.txt" in result
    
    @pytest.mark.asyncio
    async def test_run_command_blocked_dangerous(self):
        """Dangerous commands should be blocked."""
        # A command containing dangerous actions should fail validation
        result = await mcp_bridge.run_command("rm -rf /")
        assert "blocked" in result.lower() or "error" in result.lower() or "invalid" in result.lower()
    
    @pytest.mark.asyncio
    async def test_run_command_allowed_safe(self):
        """Safe commands should be allowed."""
        result = await mcp_bridge.run_command("echo hello")
        assert isinstance(result, str)
