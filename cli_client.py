"""
AI Trading CLI - Simple Command Line Interface
No authentication, no database, just direct AI chat
"""
import requests
import sys
from colorama import init, Fore, Style

# Initialize colorama for Windows
init(autoreset=True)

BACKEND_URL = "http://localhost:8000"
PASSWORD = "Preet@1246"

def print_banner():
    """Print welcome banner"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}    AI TRADING PREDICTION MODEL - CLI")
    print(f"{Fore.CYAN}{'='*60}\n")

def verify_password():
    """Simple password verification"""
    print(f"{Fore.YELLOW}Enter password to start: ", end="")
    password = input()

    if password != PASSWORD:
        print(f"{Fore.RED}❌ Incorrect password!")
        sys.exit(1)

    print(f"{Fore.GREEN}✅ Access granted!\n")

def check_backend():
    """Check if backend is running"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=3)
        if response.status_code == 200:
            print(f"{Fore.GREEN}✅ Backend is running on {BACKEND_URL}\n")
            return True
    except requests.exceptions.RequestException:
        print(f"{Fore.RED}❌ Backend is not running!")
        print(f"{Fore.YELLOW}Please start the backend first using: start_backend.bat\n")
        return False

def chat_with_ai(query: str):
    """Send query to AI and get prediction"""
    try:
        print(f"{Fore.YELLOW}🤖 AI is thinking...\n")

        response = requests.post(
            f"{BACKEND_URL}/api/v1/cli/predict",
            json={"query": query},
            timeout=60
        )

        if response.status_code == 200:
            data = response.json()

            # Extract prediction from response
            if data.get("success"):
                prediction = data.get("prediction", "")

                print(f"{Fore.CYAN}{'='*60}")
                print(f"{Fore.GREEN}AI Response:")
                print(f"{Fore.CYAN}{'='*60}\n")
                print(f"{Fore.WHITE}{prediction}\n")
                print(f"{Fore.CYAN}{'='*60}\n")
            else:
                error_msg = data.get("message", "Unknown error")
                print(f"{Fore.RED}❌ Error: {error_msg}\n")
        else:
            print(f"{Fore.RED}❌ Server error: {response.status_code}\n")

    except requests.exceptions.Timeout:
        print(f"{Fore.RED}❌ Request timeout. AI took too long to respond.\n")
    except requests.exceptions.RequestException as e:
        print(f"{Fore.RED}❌ Connection error: {str(e)}\n")
    except Exception as e:
        print(f"{Fore.RED}❌ Error: {str(e)}\n")

def main():
    """Main CLI loop"""
    print_banner()

    # Verify password
    verify_password()

    # Check backend
    if not check_backend():
        sys.exit(1)

    print(f"{Fore.CYAN}Ready to chat! Type your trading questions below.")
    print(f"{Fore.YELLOW}Commands: 'exit', 'quit', or Ctrl+C to stop\n")

    # Chat loop
    while True:
        try:
            # Get user input
            print(f"{Fore.MAGENTA}You: ", end="")
            query = input()

            # Check for exit commands
            if query.lower() in ['exit', 'quit', 'q']:
                print(f"\n{Fore.CYAN}Goodbye! Happy trading! 📈\n")
                break

            # Skip empty queries
            if not query.strip():
                continue

            # Send to AI
            chat_with_ai(query)

        except KeyboardInterrupt:
            print(f"\n\n{Fore.CYAN}Goodbye! Happy trading! 📈\n")
            break
        except Exception as e:
            print(f"{Fore.RED}Error: {str(e)}\n")

if __name__ == "__main__":
    main()
