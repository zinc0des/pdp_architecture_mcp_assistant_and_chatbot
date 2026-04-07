import sys
import argparse
from pdp_dev_mcp import __version__
from pdp_dev_mcp.common import logger
from pdp_dev_mcp.mcp_instance import mcp


def main() -> None:
    # Parse command-line arguments before starting server
    parser = argparse.ArgumentParser(
        description="PDP Development MCP Server - AI-assisted development tools"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"pdp-dev-mcp {__version__}",
    )
    parser.add_argument(
        "--transport",
        default="stdio",
        choices=["stdio"],
        help="Transport mechanism (currently only stdio is supported)",
    )
    
    args = parser.parse_args()
    
    # writing to stderr because stdout is used for the transport
    # and we want to see the logs in the console
    logger.info("Starting PDP DEV MCP server")
    logger.info(f"Version: {__version__}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Platform: {sys.platform}")

    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
