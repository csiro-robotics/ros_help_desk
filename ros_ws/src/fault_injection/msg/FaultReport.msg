# Fault Report Message
# Used to report detailed statistics and student analysis

Header header
string scenario_name      # Name of the fault injection scenario
float32 elapsed_time      # Time since fault injection started
bool scenario_completed   # True if the scenario has finished
FaultStatus[] active_faults # Array of currently active faults
int32 total_faults_injected # Total number of faults injected
string student_notes      # Space for student observations
bool fault_detected       # True if student has detected the fault
string detection_method   # How the fault was detected
float32 detection_time    # Time taken to detect the fault 