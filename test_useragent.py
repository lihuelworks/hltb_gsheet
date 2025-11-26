"""
Test fake_useragent behavior
"""
from fake_useragent import UserAgent

ua = UserAgent()

print("Testing fake_useragent...")
print("=" * 80)
print(f"Version: 2.2.0")
print()

# Generate a few user agents
for i in range(5):
    agent = ua.random
    print(f"{i+1}. {agent}")
    print(f"   Stripped: '{agent.strip()}'")
    print()

# Test the one used in the library
print("=" * 80)
print("Testing stripped vs non-stripped:")
print("=" * 80)
agent = ua.random
print(f"Original length: {len(agent)}")
print(f"Stripped length: {len(agent.strip())}")
print(f"Has leading/trailing whitespace: {agent != agent.strip()}")
