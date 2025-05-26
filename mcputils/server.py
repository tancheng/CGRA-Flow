from fastmcp import FastMCP
import subprocess
import os

# Initialize the MCP server
server = FastMCP("My MCP Server")

@server.tool()
def greet(name: str) -> str:
    return f"Hello, {name}!"

@server.tool()
def launch_cgra_ui(multi_rows: int, multi_cols: int, per_cgra_rows: int, per_cgra_cols: int, theme: str = "dark") -> str:
    """
    Launch the CGRA UI with the specified configuration.

    Args:
        multi_rows (int): Number of rows in the Multi-CGRA.
        multi_cols (int): Number of columns in the Multi-CGRA.
        per_cgra_rows (int): Number of rows in each CGRA.
        per_cgra_cols (int): Number of columns in each CGRA.
        theme (str): Theme for the UI ("dark" or "light").

    Returns:
        str: Status message indicating success or failure.
    """
    try:
        # Construct the command to launch the UI

        print("Launching CGRA UI with parameters:")
        command = (
            'bash -c "'
            "source ../venv/bin/activate && "
            "export DISPLAY=10.0.0.230:0 && "
            f"python mode_dark_light.py "
            f"--multi_rows {multi_rows} "
            f"--multi_cols {multi_cols} "
            f"--rows {per_cgra_rows} "
            f"--cols {per_cgra_cols} "
            f"--theme {theme}"
            '"'
        )
        subprocess.Popen(command, shell=True, cwd=os.path.join(os.path.dirname(__file__), ".."))

        return "CGRA UI launched successfully."
    except Exception as e:
        return f"Failed to launch CGRA UI: {str(e)}"

# Start the server
if __name__ == "__main__":
    print("Starting MCP server...")
    server.run(transport='stdio')

