#!/usr/bin/env python3
import json
import gradio as gr
import rospy
from datetime import datetime
from threading import Thread
from queue import Queue
import re
import os
import sys
import signal
import inspect
import numpy as np

# Optional dotenv import
try:
    import dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

from penguinpi_control import PenguinPiAgent
from penguinpi_prompts import get_prompts
from rosa import RobotSystemPrompts


def make_next_page_visible(num_false: int, num_true: int):
    updates = [gr.update(visible=False) for _ in range(num_false)]
    updates.extend([gr.update(visible=True) for _ in range(num_true)])
    return tuple(updates)
    # output make current page invisible and next page visible
    return gr.update(visible=False), gr.update(visible=True)

import time
import csv
# participant_id = int(time.time())
# start_times = {}
# times_spent = {}
# beginning = time.time()
# urls = {}
headers = ["participant_id"]
# data = [participant_id]
# folder = os.path.join(os.getcwd(), 'ParticipantData', str(participant_id))
# os.mkdir(folder)
# filename = f'{folder}/answers.csv'

def consent_page(title="Consent Form"):
    with gr.Column(elem_id=title, visible=True) as page:
        gr.Markdown(f"# {title}")
        gr.Markdown("""
                    ## ROS-Help-Desk – Learning Support Study    
                    
                    I have been invited to participate in the research described above. I have read and understood the Explanatory Statement and I hereby consent to take part in this study. By ticking the box below, you consent to:
                    
                        - Provide basic non-identifying personal data (e.g., ROS experience level, confidence ratings).
                        
                        - Interact with a simulated robot using the Robot Operating System (ROS).
                        
                        - Complete a series of tasks involving robot navigation, sensor inspection, fault diagnosis and debugging.
                        
                        - Use two support tools (ROS-Help-Desk and a baseline system) to complete tasks.
                        
                        - Provide inputs using a keyboard, mouse, natural language queries and written code.
                        
                        - Answer short surveys before and after the session about your experience.
                        
                        - Allow your anonymized interaction of the study to be logged and screen recorded.
                        
                        - Allow your anonymized data (e.g., task performance, queries, survey responses, time taken) to be used in academic publications and made publicly available.
                        
                        - Allow your anonymized data to be shared with collaborating research institutions.
                        
                        - Allow your anonymized data to be retained indefinitely for future research purposes.
                        
                        - Understand that your anonymized interaction data will be made publicly accessible through research repositories for transparency and reproducibility.
                        
                    Due to the anonymous nature of the data, it will not be possible to withdraw submitted responses after the study concludes. Further details about confidentiality, data storage, and your role in the study are provided in the Explanatory Statement.""")
        consent_button = gr.Button("I hereby consent to take part in this study", variant= 'stop')
    return page, consent_button

def inst_page(title="Instructions for the User"):
    with gr.Column(elem_id=title, visible=False) as page:
        gr.Markdown(f"# {title}")
        gr.Markdown("""
                    ## Introduction

                    Welcome to our study! We are investigating how a new AI-powered tool, the "ROS-Help-Desk," can make learning the Robot Operating System (ROS) easier and faster. Your participation will provide valuable feedback to help us improve this learning tool.

                    ## What is this study about?

                    This study has two main parts. 
                    1. First, you will have the opportunity to learn fundamental ROS concepts using our new ROS-Help-Desk. 
                    2. In the second part, you will apply what you've learned to complete a surveillance task using two different AI assistance tools.

                    ## What will I be asked to do?

                    The study will proceed in the following stages:

                    1. **Pre-Study Survey**: You will begin by completing a brief survey to gather information about your current experience with robotics and programming.

                    2. **Familiarization & Learning**:

                    You will be introduced to the ROS-Help-Desk, an AI tool designed to help work with ROS.
                    We will provide you with a list of introductory tasks, such as moving a simulated robot and interpreting its sensor data. These tasks are designed to guide your learning.
                    While we provide a structured list, you are encouraged to explore and ask the ROS-Help-Desk any questions you have about ROS to deepen your understanding.

                    3. **Mid-Study Survey**: Following the learning phase, you will complete a short survey about your experience using the ROS-Help-Desk.

                    4. **Surveillance Tasks**:

                    You will be asked to complete two similar but distinct "surveillance" tasks. In each, you will navigate a robot through a maze-like virtual environment and count the number of specific objects you find.
                    For one task, you will have access to the ROS-Help-Desk.
                    For the other task, you will use a standard chatbot interface (like a general-purpose LLM).
                    The order in which you use these two tools will be randomized to ensure fairness.""")
    
                    # ("""This study is designed to help you learn ROS (Robot Operating System) concepts more easily and quickly using a new AI-powered support tool called the ROS-Help-Desk. 
                    # After the pre-survey, you will begin by familiarising yourself with key ROS concepts using the ROS-Help-Desk, 
                    # while completing a series of tasks such as moving the robot and inspecting its sensor data. 
                    # These tasks will be given in a form of a list. You are free to go `off script' and test the system to improve you learning and understanding of ROS.
                    
                    # Then, you will complete a short survey about your experience. 
                    
                    # In the second stage you will complete two survelliance tasks where you are to navigate the robot in the given maze environment using keyboard and the counting how many objects you encounter. 
                    # The environment and objects will be differnet in the two tasks but with similar difficulty.
                    # In one task you will get the help of ROS-Help-Desk, and the other you will have a standard LLM chat-interface. 
                    # These would be given in random order. """)
        next_button = gr.Button("I understand my tasks, let's get started", variant= 'stop')
    return page, next_button

def demographic_page(title='Demographic page'):
    with gr.Column(elem_id=title, visible=False) as page:
        with gr.Tab("📝 ROS Knowledge & Experience"):
            gr.Markdown("## ROS Knowledge & Experience")
            experience = gr.Radio(
                ["No experience", "Basic (tutorials only)", "Intermediate (small projects)", "Advanced (complex systems)"],
                label="What is your current level of experience with ROS?",
                value="No experience",
            )
            ros_conf= gr.Slider(
                minimum=1,
                maximum=5,
                step=1,
                label="How confident are you in working with ROS systems?",
                info="1: Not confident at all, 5: Very confident",
                interactive=True
            )
            debugging_conf= gr.Slider(
                minimum=1,
                maximum=5,
                step=1,
                label="How confident are you in debugging ROS systems?",
                info="1: Not confident at all, 5: Very confident",
                interactive=True
            )
            ros_concepts = gr.CheckboxGroup(
                ["Nodes", "Topics", "Services", "Actions", "Parameters", "Launch files", "Packages", "None of these", "Other-specify"],
                label="Which ROS concepts are you most familiar with?"
            )

        with gr.Tab("💡 Problem-Solving"):
            gr.Markdown("### Problem-Solving")
            solving_method = gr.CheckboxGroup(
                ["Ask instructor/peers", "Search online", "Read documentation", "Trial and error", "Other"],
                label="When you encounter programming errors, how do you typically resolve them?",
                interactive=True
            )
            solving_conf = gr.Slider(
                minimum=1,
                maximum=5,
                step=1,
                label="How confident are you in diagnosing technical issues independently?",
                info="1: Not confident at all, 5: Very confident",
                interactive=True
            )

        with gr.Tab("🛠️ Tool Experience and Expected Usage"):
            gr.Markdown("## Tool Experience and Expected Usage")
            tool_freq = gr.Radio(
                ["Never", "Rarely", "Sometimes", "Frequently"],
                label="Have you used AI-based support tools before?",
                value="Never",
                interactive=True
            )
            
            primary_task = gr.Dropdown(
                ['learning_basics', 'navigation', 'computer_vision', 'system_diagnostics'], 
                label="What do you think is the primary task you will use PenguinPi Agent for", 
                info="Please select your primary robotics task"
            )
            
            learning_hope = gr.Textbox(
                label="What do you hope to learn from this activity?",
                lines=3,
                placeholder="Type your answer here...",
                interactive=True
            )
            
        user_details_btn = gr.Button("Submit", variant= 'stop')
        
        all_input =  [experience,  ros_conf,  debugging_conf,  ros_concepts,  solving_method,  solving_conf,  tool_freq,  primary_task, learning_hope, user_details_btn]
        data_entries = {'experience': experience, 'ros_conf': ros_conf, 'debugging_conf': debugging_conf, 'ros_concepts': ros_concepts, 'solving_method': solving_method, 'solving_conf': solving_conf, 'tool_freq': tool_freq, 'primary_task': primary_task, 'learning_hope':learning_hope, 'user_details_btn':user_details_btn}
    return page, all_input

def post_survey_page(title='Post survey page'):
    ros_concepts_list = [
        "Nodes",
        "Topics",
        "Messages",
        "Services",
        "Actions",
        "Launch Files",
        "Parameters",
        "TF (Transformations)",
        "URDF (Robot Models)"
    ]
    with gr.Column(elem_id=title, visible=False) as page:
        # --- Learning Outcomes Section ---
        with gr.Tab("📝 Learning Outcomes"):
            gr.Markdown("## Learning Outcomes")
            q1 = gr.Slider(
                minimum=1,
                maximum=5,
                step=1,
                label="1. Rate your understanding of ROS concepts after using the tool.",
                info="1 = Much worse, 5 = Much better",
                interactive=True
            )
            q2 = gr.CheckboxGroup(
                ros_concepts_list,
                label="2. Which ROS concepts did you learn most about during this activity?",
                info="Check all that apply."
            )
            q3 = gr.Slider(
                minimum=1,
                maximum=5,
                step=1,
                label="3. How well did the tool help you understand the relationships between different ROS components?",
                info="1 = Not well at all, 5 = Very well",
                interactive=True
            )

        # --- Problem-Solving Effectiveness Section ---
        with gr.Tab("💡 Problem-Solving"):
            gr.Markdown("## Problem-Solving Effectiveness")
            q4 = gr.Slider(
                minimum=1,
                maximum=5,
                step=1,
                label="4. How effectively did the tool help you complete your assigned tasks?",
                info="1 = Not effective at all, 5 = Very effective",
                interactive=True
            )
            q5 = gr.Slider(
                minimum=1,
                maximum=5,
                step=1,
                label="5. How helpful was the tool in diagnosing and resolving errors?",
                info="1 = Not helpful at all, 5 = Very helpful",
                interactive=True
            )
            q6 = gr.Slider(
                minimum=1,
                maximum=5,
                step=1,
                label="6. Do you feel more confident in debugging ROS systems after this activity?",
                info="1 = Much less confident, 5 = Much more confident",
                interactive=True
            )
            q7 = gr.Textbox(
                lines=3,
                label="7. How has your approach to problem-solving in ROS changed, if at all?",
                placeholder="Please describe any changes in your thought process or strategy..."
            )

        # --- Usability Section ---
        with gr.Tab("🖱️ Usability"):
            gr.Markdown("## Usability")
            q8 = gr.Slider(
                minimum=1,
                maximum=5,
                step=1,
                label="8. How easy was the tool to use overall?",
                info="1 = Very difficult, 5 = Very easy",
                interactive=True
            )
            gr.Markdown("### System Usability Scale (SUS)")
            gr.Markdown("For the following 10 statements, please rate how much you agree or disagree.")
            # Placeholder for the 10 standard SUS questions
            # sus_questions = []
            # for i in range(1, 11):
            #     sus_q = gr.Radio(
            #         ["1", "2", "3", "4", "5"],
            #         label=f"SUS Question {i}: [Insert Standard SUS Question {i} Text Here]",
            #         info="1 = Strongly Disagree, 5 = Strongly Agree"
            #     )
            #     sus_questions.append(sus_q)

            q9 = gr.Slider(
                minimum=1,
                maximum=5,
                step=1,
                label="9. How intuitive did you find the tool's interface?",
                info="1 = Not intuitive at all, 5 = Very intuitive",
                interactive=True
            )
            q10 = gr.Slider(
                minimum=1,
                maximum=5,
                step=1,
                label="10. How quickly were you able to get useful help from the tool?",
                info="1 = Very slowly, 5 = Very quickly",
                interactive=True
            )

        # --- Overall Experience Section ---
        with gr.Tab("⭐ Overall Experience"):
            gr.Markdown("## Overall Experience")
            q11 = gr.Textbox(
                lines=3,
                label="11. What did you like most about the tool?",
                placeholder="Describe the most positive aspects of your experience..."
            )
            q12 = gr.Textbox(
                lines=3,
                label="12. What could be improved about the tool?",
                placeholder="Please provide any suggestions for improvement..."
            )
            q13_choice = gr.Radio(
                ["Yes", "No"],
                label="13. Would you use this tool again for future ROS projects?"
            )
            q13_exp = gr.Textbox(
                lines=2,
                label="Please briefly explain why.",
                placeholder="Explanation..."
            )
            q14 = gr.Slider(
                minimum=1,
                maximum=5,
                step=1,
                label="14. How likely are you to recommend this tool to other ROS learners?",
                info="1 = Very unlikely, 5 = Very likely",
                interactive=True
            )
        post_answer_btn = gr.Button("Submit", variant= 'stop')
        all_inputs = [q1, q2, q3, q4, q5, q6, q7, q8] + [q9, q10, q11, q12, q13_choice, q13_exp, q14] + [post_answer_btn]
        

    return page, all_inputs

def final_page(title="Thank you"):
    with gr.Column(elem_id=title, visible=False) as page:
        gr.Markdown(f"# {title}")
        gr.Markdown("### Thank you for your time! Please click the below 'Finish' button to end the study.")
        complete_button = gr.Button("Finish")
        # @complete_button.click()
        # def complete_click(page=page):
        #     print("trying to exit")
        #     page.close()
    return page, complete_button

def get_inputs(node, inputs, main_tab_id):
    # Check if node is a Radio or Slider
    if isinstance(node, (gr.Radio, gr.Slider, gr.Textbox)): 
        if node.label:
            if node.label != 'User Query':
                inputs.append(node) #TODO should this be inside the if
                if node.label not in headers:
                    headers.append(f"{main_tab_id}: {node.label}")

    # If node has children, recurse on each child
    if hasattr(node, 'children'):
        for child in node.children:
            get_inputs(child, inputs, main_tab_id)


def flatten_list(lst):
    flattened = []
    for item in lst:
        if isinstance(item, tuple):
            # Replace None with 'None' in the tuple
            flat_tuple = tuple('None' if element is None else element for element in item)
            flattened.extend(flat_tuple)
        else:
            # Replace None with 'None' in the list
            flattened.append('None' if item is None else item)
    return flattened


def get_tool_definition(executor_tools, tool_name, summary):
    """
    Retrieves the definition of a tool by its name.
    """
    try:
        true_index = np.where(np.asarray([tool_name in tool.name for tool in executor_tools]))[0][0]
        tool = executor_tools[true_index]
        if hasattr(tool, 'func') and callable(tool.func):
            try:
                source_code = inspect.getsource(tool.func)
            except TypeError:
                source_code = "Source code not available (e.g., built-in or dynamically defined)."    
        summary += (
            f"**Tool description:** `{tool.description}`\n"
            f"**Tool source code:**\n```python\n{source_code}\n```\n"
        )
    except:
        summary += (
            f"**Tool description:** Could not be found\n"
        )
    return summary
    
def get_invoked_tools_summary(executor_tools, result):
    """
    Extracts and formats a summary of the invoked tools and their definitions.
    """
    if "intermediate_steps" not in result:
        return "No tools were invoked for this request."

    tool_summary = []
    for agent_action, tool_output in result["intermediate_steps"]:
        tool_name = agent_action.tool
        tool_input = agent_action.tool_input
        summary = (
            f"**Tool:** `{tool_name}`\n"
            f"**Tool Input:** `{tool_input}`\n"
            f"**Tool Output:** `{tool_output}`\n"
        )
        
        # Find the tool's definition
        summary = get_tool_definition(executor_tools, tool_name, summary)

        tool_summary.append(summary)

    return "\n".join(tool_summary)


class PenguinPiAgentGradio:
    def __init__(self, penguinpi_agent):
        """
        Wrap the original PenguinPiAgent with Gradio functionality
        
        Args:
            penguinpi_agent: The original PenguinPiAgent instance
        """
        self.agent = penguinpi_agent
        self.message_history = []
        self.response_queue = Queue()
        self.ros_thread = None
        
        # Copy over important attributes from the original agent
        self.examples = self.agent.examples
        self.command_handler = self.agent.command_handler
        
        # Initialize user preferences
        self.user_experience = 'intermediate'
        self.primary_task = 'learning_basics'
        self.user_based_prompt = ""
        
        # Collect information 
        self.data = []
        
        # Ensure command handlers are adapted for Gradio
        self._adapt_command_handlers()
    
    def _adapt_command_handlers(self):
        """Adapt command handlers for the Gradio interface"""
        # Store original handlers
        original_handlers = dict(self.command_handler)
        
        # Replace them with Gradio-compatible versions
        self.command_handler = {
            "examples": self.show_examples,
            "clear": self.clear_chat,
            "status": self.get_robot_status_direct,
            "pose": self.get_robot_pose_direct
        }
        
        # Add the info handler if it exists
        if "info" in original_handlers:
            self.command_handler["info"] = self.show_event_details
    
    def create_interface(self):            
        """Create the Gradio interface for the PenguinPi Agent"""
        rospy.loginfo("Creating Gradio interface...")
        
        with gr.Blocks(title="PenguinPi Agent", theme=gr.themes.Base()) as interface:
            rospy.loginfo("Created Gradio Blocks...")
            
            gr.Markdown("# 🐧 PenguinPi Agent")
            
            # Greet
            gr.Markdown("### Hi! I'm the PenguinPi Agent: your personal assistant for learning robotics and controlling the PenguinPi robot!")
            
            # Page 2 - Main interface
            with gr.Column(visible=True) as page2:
                # Chat interface
                chatbot = gr.Chatbot(label="Conversation", height=500, type="messages")
                
                with gr.Row():
                    user_input = gr.Textbox(
                        label="Type a question, command, or 'exit'",
                        placeholder="Enter your query here...",
                        show_label=True
                    )
                    submit_btn = gr.Button("Submit")
                
                # Command information
                available_commands = ", ".join(self.command_handler.keys())
                gr.Markdown(f"You can choose the following commands if not certain of what to do: {available_commands} or exit")
                
                # Command buttons
                with gr.Row():
                    examples_btn = gr.Button("examples")
                    clear_btn = gr.Button("clear")
                    status_btn = gr.Button("status")
                    pose_btn = gr.Button("pose")
                    info_btn = gr.Button("info", visible="info" in self.command_handler)
                    exit_btn = gr.Button("Exit")
                
                # Example selection dropdown (initially hidden)
                with gr.Row(visible=False) as example_row:
                    example_dropdown = gr.Dropdown(
                        choices=self.examples,
                        label="Select an example",
                        value=self.examples[0] if self.examples else None
                    )
                    use_example_btn = gr.Button("Use Example")
                
                # Event details (initially hidden)
                with gr.Row(visible=False) as event_details_row:
                    event_details = gr.JSON(label="Event Details")
            
            # Robot status monitoring
            with gr.Column(visible=True) as status_column:
                gr.Markdown("I need to write something to explain this box")
                status_box = gr.Text("Robot Status: Initializing...", label="Real-time Robot Status")
                health_button = gr.Button('Check System Health')
            
            rospy.loginfo("Created status monitoring elements...")

            
            
            # Main input handlers
            submit_btn.click(
                fn=self.process_input,
                inputs=[user_input, chatbot],
                outputs=[user_input, chatbot]
            )
            
            user_input.submit(
                fn=self.process_input,
                inputs=[user_input, chatbot],
                outputs=[user_input, chatbot]
            )
            
            # Command button handlers
            examples_btn.click(
                fn=lambda history: (history, gr.update(visible=True), gr.update(visible=False)),
                inputs=[chatbot],
                outputs=[chatbot, example_row, event_details_row]
            )
            
            clear_btn.click(
                fn=self.clear_chat,
                outputs=[chatbot, example_row, event_details_row]
            )
            
            status_btn.click(
                fn=self.run_status_command,
                inputs=[chatbot],
                outputs=[chatbot]
            )
            
            pose_btn.click(
                fn=self.run_pose_command,
                inputs=[chatbot],
                outputs=[chatbot]
            )
            
            if "info" in self.command_handler:
                info_btn.click(
                    fn=self.show_event_details,
                    inputs=[chatbot],
                    outputs=[chatbot, example_row, event_details_row, event_details]
                )
            
            exit_btn.click(
                fn=self.exit_application,
                inputs=[chatbot],
                outputs=[chatbot]
            )
            
            # Example selection handler
            use_example_btn.click(
                fn=self.use_example,
                inputs=[example_dropdown, chatbot],
                outputs=[user_input, chatbot, example_row]
            )
            
            # Health check
            health_button.click(
                fn=self.check_system_health,
                outputs=[status_box]
            )
            
            # Auto-update status
            interface.load(
                fn=self.update_status,
                outputs=[status_box]
            )
            
        rospy.loginfo("Gradio interface created successfully!")
        return interface
    
    def update_agent(self, experience, ros_conf, debugging_conf, ros_concepts, solving_method, solving_conf, tool_freq, primary_task, learning_hope, user_details_btn):
        """Update agent based on user experience and task"""
        # Store user preference        
        # Generate custom prompts based on user preferences
        self.user_based_prompt = self._generate_user_prompt(experience, primary_task)
        
        return gr.update(visible=False), gr.update(visible=True), gr.update(visible=True)
    
    def process_input(self, user_text, history):
        """Process user input and update the chat history"""
        if not user_text.strip():
            return "", history
        
        # Ensure history is a list of dictionaries
        if not isinstance(history, list):
            history = []
        
        # Process built-in commands
        if user_text in self.command_handler:
            result, _, _ = self.run_command(history, command=user_text)
            return "", result
        
        # Add user message to history
        history.append({"role": "user", "content": user_text})
        
        # Process exit command
        if user_text.lower() == "exit":
            history.append({"role": "assistant", "content": "Exiting the application. You can close this window."})
            return "", history
        
        # Process regular queries
        unfiltered_response = self.agent.invoke(user_text)
        tools_summary = get_invoked_tools_summary(self.agent._ROSA__executor.tools, unfiltered_response)
        if isinstance(unfiltered_response, dict):
            unfiltered_response = unfiltered_response['output']
        response = self.filter_and_rewrite_output(unfiltered_response, self.user_based_prompt)
        if tools_summary != '':
            response += f"""\n\n### Tool Inovation Summary \n {tools_summary}"""  
                        
        # try:
        #     # Create enhanced prompt with user context
        #     enhanced_prompt = f"""
        #     {self.user_based_prompt}
            
        #     User Query: {user_text}
            
        #     Current robot state:
        #     - Position: ({self.agent.x:.2f}, {self.agent.y:.2f})
        #     - Orientation: {self.agent.theta:.2f} radians ({self.agent.theta * 180 / 3.14159:.1f} degrees)
        #     - Left encoder: {self.agent.encoder_left:.2f}
        #     - Right encoder: {self.agent.encoder_right:.2f}
        #     - Camera available: {self.agent.latest_image is not None}
            
        #     Please provide a helpful, educational response appropriate for the user's experience level.
        #     """
            
        #     # Get response from agent
        #     unfiltered_response = self.agent.invoke(enhanced_prompt)
        #     tools_summary = get_invoked_tools_summary(self.agent._ROSA__executor.tools, unfiltered_response)
        #     if isinstance(unfiltered_response, dict):
        #         unfiltered_response = unfiltered_response['output']
        #     response = self.filter_and_rewrite_output(unfiltered_response, self.user_based_prompt)
        #     if tools_summary != '':
        #         response += f"""\n\n### Tool Inovation Summary \n {tools_summary}"""            
        # except Exception as e:
        #     response = f"Error processing request: {str(e)}"
        
        # Update history with response
        history.append({"role": "assistant", "content": response})
        return "", history
    
    def filter_and_rewrite_output(self, final_answer, user_prompt):
        """Filter and rewrite outputs based on user experience level"""
        # Simple filtering logic for now
        filtered_answer = final_answer.strip()
        
        # If we have user-specific prompts, we could enhance the response here
        if user_prompt and self.user_experience == 'beginner':
            # Add more explanatory content for beginners
            composite_prompt = f"""
            User Experience Level: {self.user_experience}
            Primary Task: {self.primary_task}
            
            Original Answer: {filtered_answer}
            
            Please rewrite this answer to be more suitable for a {self.user_experience} user interested in {self.primary_task}.
            Make it more educational and add explanations where needed.
            """
            try:
                refined_answer = self.agent.invoke(composite_prompt)
                return refined_answer
            except:
                return filtered_answer
        
        return filtered_answer
    
    def run_command(self, history, command):
        """Run a command from the command handler"""
        if not isinstance(history, list):
            history = []
        
        # Add command to history
        history.append({"role": "user", "content": command})
        
        # Run the command
        try:
            if command == "examples":
                # This just shows the example dropdown, handled separately
                history.append({"role": "assistant", "content": "Please select an example from the dropdown below."})
                return history, gr.update(visible=True), gr.update(visible=False)
                
            elif command == "clear":
                return self.clear_chat()
                
            elif command == "status":
                response = self.get_robot_status_direct()
                history.append({"role": "assistant", "content": response})
                return history, gr.update(visible=False), gr.update(visible=False)
                
            elif command == "pose":
                response = self.get_robot_pose_direct()
                history.append({"role": "assistant", "content": response})
                return history, gr.update(visible=False), gr.update(visible=False)
                
            elif command == "info" and hasattr(self.agent, "last_events"):
                return self.show_event_details(history)
                
            else:
                # Generic command handling
                response = "Command executed."
                history.append({"role": "assistant", "content": response})
                return history, gr.update(visible=False), gr.update(visible=False)
                
        except Exception as e:
            response = f"Error executing command '{command}': {str(e)}"
            history.append({"role": "assistant", "content": response})
            return history, gr.update(visible=False), gr.update(visible=False)
    
    def run_status_command(self, history):
        """Run status command and update chat"""
        if not isinstance(history, list):
            history = []
        
        history.append({"role": "user", "content": "status"})
        response = self.get_robot_status_direct()
        history.append({"role": "assistant", "content": response})
        return history
    
    def run_pose_command(self, history):
        """Run pose command and update chat"""
        if not isinstance(history, list):
            history = []
        
        history.append({"role": "user", "content": "pose"})
        response = self.get_robot_pose_direct()
        history.append({"role": "assistant", "content": response})
        return history
    
    def show_examples(self, history):
        """Show the examples dropdown"""
        if not isinstance(history, list):
            history = []
        
        # Add the example message in correct format
        history.append({"role": "user", "content": "examples"})
        history.append({"role": "assistant", "content": "Please select an example from the dropdown below."})

        return history, gr.update(visible=True), gr.update(visible=False)
    
    def use_example(self, selected_example, history):
        """Use the selected example"""
        if not isinstance(history, list):
            history = []
        
        if not selected_example:
            return "", history, gr.update(visible=False)
        
        # Add the selected example to history and process it
        history.append({"role": "user", "content": selected_example})

        # Process the example as a regular query
        try:
            unfiltered_response = self.agent.invoke(selected_example)
        except Exception as e:
            response = f"Error processing example: {str(e)}"
        
        tools_summary = get_invoked_tools_summary(self.agent._ROSA__executor.tools, unfiltered_response)
        
        if isinstance(unfiltered_response, dict):
            unfiltered_response = unfiltered_response['output']
            
        response = self.filter_and_rewrite_output(unfiltered_response, self.user_based_prompt)
        
        if tools_summary != '':
            response += f"""\n\n### Tool Inovation Summary \n {tools_summary}"""  
            
        # Append the response from the assistant
        history.append({"role": "assistant", "content": response})

        # Hide the example dropdown
        return "", history, gr.update(visible=False)
        
    def clear_chat(self):
        """Clear the chat history"""
        try:
            # Reset message history
            self.message_history = []
            
            # Reset event history if it exists
            if hasattr(self.agent, "last_events"):
                self.agent.last_events = []
            
            # Clear command handler for info if it exists
            if "info" in self.command_handler:
                self.command_handler.pop("info", None)
                
        except Exception as e:
            rospy.logerr(f"Error clearing chat: {str(e)}")
        
        # Return empty history and hide dropdowns
        return [], gr.update(visible=False), gr.update(visible=False)
    
    def show_event_details(self, history):
        """Show details about the last events"""
        if not isinstance(history, list):
            history = []

        if not hasattr(self.agent, "last_events") or not self.agent.last_events:
            history.append({"role": "user", "content": "info"})
            history.append({"role": "assistant", "content": "No event details available."})
            return history, gr.update(visible=False), gr.update(visible=False), []
        
        # Format event details for display
        event_details = self.agent.last_events
        
        # Add formatted response to history
        history.append({"role": "user", "content": "info"})
        history.append({"role": "assistant", "content": "Event details are displayed below."})

        # Show the event details panel
        return history, gr.update(visible=False), gr.update(visible=True), event_details
    
    def exit_application(self, history):
        # Signal to shutdown ROS node in a separate thread to avoid blocking
        shutdown_thread = Thread(target=self._complete_shutdown)
        shutdown_thread.daemon = True
        shutdown_thread.start()
        
        if history is not None:
            if not isinstance(history, list):
                history = []
        
            history.append({"role": "user", "content": "exit"})
            history.append({"role": "assistant", "content": "Exiting the application. You can close this window."})
            return history
 
    def _complete_shutdown(self):
        """Complete shutdown sequence with a small delay to allow UI update"""
        import time
        
        # Small delay to allow UI to update
        time.sleep(0.5)
        
        try:
            # Shutdown robot safely
            if self.agent:
                self.agent.penguinpi_tools._stop_robot()
            
            # Shutdown ROS
            rospy.signal_shutdown("User requested exit")
            
            # Force exit the program
            os._exit(0)
        except Exception as e:
            rospy.logerr(f"Error during shutdown: {e}")
            os._exit(1)
    
    def get_robot_status_direct(self):
        """Get robot status without using LangChain tools"""
        try:
            status_info = f"""Robot Status:
                - Position: ({self.agent.x:.2f}, {self.agent.y:.2f})
                - Orientation: {self.agent.theta:.2f} rad ({self.agent.theta * 180 / 3.14159:.1f}°)
                - Left encoder: {self.agent.encoder_left:.2f}
                - Right encoder: {self.agent.encoder_right:.2f}
                - Camera available: {self.agent.latest_image is not None}
                - ROS node running: {not rospy.is_shutdown()}"""
            return status_info
        except Exception as e:
            return f"Error getting status: {str(e)}"
    
    def get_robot_pose_direct(self):
        """Get robot pose without using LangChain tools"""
        return f"Current position: ({self.agent.x:.2f}, {self.agent.y:.2f}), orientation: {self.agent.theta:.2f} rad ({self.agent.theta * 180 / 3.14159:.1f}°)"
    
    def check_system_health(self):
        """Check system health"""
        try:
            health_info = f"""System Health Check:
                - ROS Master: {'Running' if not rospy.is_shutdown() else 'Not Running'}
                - Agent Node: Running
                - Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                - Position: ({self.agent.x:.2f}, {self.agent.y:.2f})
                - Orientation: {self.agent.theta:.2f} rad ({self.agent.theta * 180 / 3.14159:.1f}°)
                - Encoders: L={self.agent.encoder_left:.2f}, R={self.agent.encoder_right:.2f}
                - Camera available: {self.agent.latest_image is not None}"""
            return health_info
        except Exception as e:
            return f"Error checking system health: {str(e)}"
    
    def update_status(self):
        """Update robot status"""
        return self.get_robot_status_direct()
    
    def _generate_user_prompt(self, experience, primary_task):
        """Generate user-specific prompt based on experience and task"""
        experience_prompts = { #Todo there are 4 now
            'beginner': "You are helping a beginner who is new to robotics. Provide detailed explanations, use simple language, and focus on educational content. Always explain what each command does and why.",
            'intermediate': "You are helping someone with some robotics experience. Provide moderate explanations and focus on practical applications. You can use more technical terms but still explain complex concepts.",
            'expert': "You are helping an experienced robotics user. You can use technical language and focus on advanced features and optimization. Provide concise, professional responses."
        }
        
        task_prompts = {
            'learning_basics': "Focus on teaching fundamental robotics concepts, sensor operation, and basic movement commands. Provide step-by-step explanations.",
            'navigation': "Emphasize navigation techniques, path planning, and position control. Help with complex movement patterns.",
            'computer_vision': "Focus on camera analysis, image processing, object detection, and visual navigation. Explain computer vision concepts.",
            'system_diagnostics': "Emphasize system monitoring, error detection, troubleshooting, and performance optimization. Help with debugging and maintenance."
        }
        
        base_prompt = f"""
        {experience_prompts.get(experience, experience_prompts['intermediate'])}
        {task_prompts.get(primary_task, task_prompts['learning_basics'])}
        
        Remember: You are the PenguinPi robot, a compact educational mobile robot. Always prioritize safety and provide educational value.
        """
        
        return base_prompt
    
    def robot_system_prompts_to_string(self, prompts: RobotSystemPrompts) -> str:
        """Convert RobotSystemPrompts to string format"""
        fields = [
            ("Embodiment and Persona", prompts.embodiment_and_persona),
            ("About Your Operators", prompts.about_your_operators),
            ("Critical Instructions", prompts.critical_instructions),
            ("Constraints and Guardrails", prompts.constraints_and_guardrails),
            ("About Your Environment", prompts.about_your_environment),
            ("About Your Capabilities", prompts.about_your_capabilities),
            ("Nuance and Assumptions", prompts.nuance_and_assumptions),
            ("Mission and Objectives", prompts.mission_and_objectives),
        ]
        
        result = "\n\n".join([f"{title}:\n{content}" for title, content in fields])
        return result
    
    def shutdown_ros(self):
        """Shutdown ROS node safely"""
        try:
            if self.agent:
                self.agent.penguinpi_tools._stop_robot()
            rospy.signal_shutdown("Gradio interface shutdown")
        except Exception as e:
            rospy.logerr(f"Error during shutdown: {e}")
    
    def toggle_streaming(self, enabled):
        """Toggle streaming mode (placeholder for PenguinPi)"""
        # PenguinPi agent doesn't currently support streaming
        rospy.loginfo(f"Streaming toggle requested: {enabled} (not implemented)")
        return None

def run_with_gradio(penguinpi_agent, prevent_thread_lock=False):
    """
    Run the PenguinPiAgent with a Gradio interface
    
    Args:
        penguinpi_agent: An initialized PenguinPiAgent instance
        prevent_thread_lock: Whether to prevent thread lock
    """
    gradio_wrapper = PenguinPiAgentGradio(penguinpi_agent)
    interface = gradio_wrapper.create_interface()
    
    try:
        rospy.loginfo("Launching Gradio interface...")
        interface.launch(
            server_name="127.0.0.1",  # Use localhost instead of 0.0.0.0
            server_port=7860,
            share=False,
            prevent_thread_lock=prevent_thread_lock,
            show_error=True,
            quiet=False,
            inbrowser=True  # Auto-open browser
        )
        
        # If prevent_thread_lock is True, we need to keep the main thread alive
        if prevent_thread_lock:
            rospy.loginfo("Gradio interface launched, keeping alive...")
            try:
                # Keep the main thread alive while ROS is running
                while not rospy.is_shutdown():
                    rospy.sleep(1.0)
            except KeyboardInterrupt:
                rospy.loginfo("Received keyboard interrupt, shutting down...")
                gradio_wrapper.shutdown_ros()
                
    except Exception as e:
        rospy.logerr(f"Error launching Gradio interface on localhost: {e}")
        rospy.loginfo("Trying alternative launch configuration...")
        try:
            # Try with share=True as fallback
            interface.launch(
                share=True,
                prevent_thread_lock=False,  # Don't prevent thread lock for fallback
                show_error=True,
                quiet=False,
                inbrowser=True
            )
        except Exception as e2:
            rospy.logerr(f"Error launching Gradio interface with share: {e2}")
            rospy.loginfo("Trying minimal configuration...")
            try:
                # Minimal configuration
                interface.launch(
                    prevent_thread_lock=False,  # Don't prevent thread lock
                    show_error=True
                )
            except Exception as e3:
                rospy.logerr(f"All Gradio launch attempts failed: {e3}")
                gradio_wrapper.shutdown_ros()
                raise e3

def main():
    """Main function for Gradio interface"""
    
    # Global reference for cleanup
    global agent_instance
    agent_instance = None
    
    def signal_handler(signum, frame):
        """Handle shutdown signals gracefully"""
        rospy.loginfo("Received shutdown signal, cleaning up...")
        if agent_instance:
            try:
                agent_instance.penguinpi_tools._stop_robot()
            except:
                pass
        rospy.signal_shutdown("User interrupt")
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Load environment variables if available
        try:
            if DOTENV_AVAILABLE:
                dotenv.load_dotenv(dotenv.find_dotenv())
        except:
            pass  # dotenv not available, continue without it
        
        rospy.loginfo("Initializing PenguinPi Agent...")
        
        # Initialize the PenguinPi agent
        agent_instance = PenguinPiAgent(streaming=False, verbose=True)
        
        rospy.loginfo("Starting Gradio interface...")
        
        # Run with Gradio interface - use blocking mode to keep interface alive
        run_with_gradio(agent_instance, prevent_thread_lock=False)
        
    except KeyboardInterrupt:
        rospy.loginfo("PenguinPi Agent Gradio interrupted by user")
        if agent_instance:
            try:
                agent_instance.penguinpi_tools._stop_robot()
            except:
                pass
    except rospy.ROSInterruptException:
        rospy.loginfo("PenguinPi Agent Gradio interrupted by ROS")
    except Exception as e:
        rospy.logerr(f"Error starting PenguinPi Agent Gradio: {e}")
        if agent_instance:
            try:
                agent_instance.penguinpi_tools._stop_robot()
            except:
                pass
    finally:
        rospy.loginfo("PenguinPi Agent Gradio shutdown complete")
        try:
            rospy.signal_shutdown("Main function exit")
        except:
            pass

if __name__ == '__main__':
    main() 