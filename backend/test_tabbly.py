from services import tabbly

try:
    agents = tabbly.get_agents()
    print("Agents:", agents)
except Exception as e:
    print("Error:", e)
