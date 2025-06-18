# Fault Status Message
# Used to report the current fault injection state

Header header
string fault_type      # "keyboard", "camera", "odometry", "joint_states"
string fault_mode      # "delay", "drop", "corruption", "noise", "freeze"
bool is_active         # True if fault is currently being injected
float32 fault_rate     # Probability of fault (0.0 to 1.0)
float32 fault_severity # Severity level (0.0 to 1.0)
int32 messages_affected # Number of messages affected since start
int32 total_messages   # Total messages processed
string description     # Human-readable description of the fault 