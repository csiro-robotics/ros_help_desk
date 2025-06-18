from langchain.tools import BaseTool
from langchain.agents import tool, Tool
from transformers import AutoProcessor, Blip2ForConditionalGeneration, BlipProcessor, BlipForConditionalGeneration, DetrImageProcessor, DetrForObjectDetection, AutoModelForVisualQuestionAnswering
import torch
from typing import Any
import PIL
import cv2
import time
import json
from typing import Optional
# ros related
import rospy
import numpy as np
import sensor_msgs.msg
#
import os
from tempfile import NamedTemporaryFile
from langchain.agents import initialize_agent
from langchain_community.chat_models import ChatOpenAI
from langchain.chains.conversation.memory import ConversationBufferWindowMemory


@tool
def save_ros_image_to_file(topic: str, output_path: Optional[str]=None, timeout: float = 5.0) -> str:
    """
    A tool to subscribe to a ros2 image topic and save the latest image to a file.
    
    Args:
        topic: ROS2 image topic to subscribe to
        output_path: Path where to save the image. If not given saving in "/tmp/ros_image.jpg"
        timeout: Maximum time to wait in seconds
        
    Returns:
        str: The path where the image was saved
    """   
    if output_path is None:
        output_path = "/tmp/ros_image.jpg"
    
    # Initialize ROS if needed
    if not rospy.core.is_initialized():
        rospy.init_node('image_saver_ros1', anonymous=True)
        rospy.loginfo("ROS node 'image_saver_ros1' initialized.")
    else:
        rospy.loginfo("ROS node already initialized, using existing context for 'image_saver_ros1' functions.")

    
    # Track if we've received an image
    image_received = False

    
    # Callback function
    def image_callback(msg):
        nonlocal image_received
        try:
            height = msg.height
            width = msg.width
            channels = 3
            cv_image = np.frombuffer(msg.data, dtype=np.uint8).reshape(height, width, channels)
            cv2.imwrite(output_path, cv_image)
            image_received = True
        except Exception as e:
            rospy.logerr(f"Error processing image: {str(e)}")
    
    # Create subscription
    rospy.Subscriber(topic, sensor_msgs.msg.Image, image_callback, queue_size=1) # queue_size=1 to get the latest message
    
    # Spin for the specified timeout
    start_time = time.time()
    while time.time() - start_time < timeout and (not image_received):
        rospy.sleep(0.1) # Process callbacks for 0.1 seconds

    
    # Return status
    if image_received:
        # return f"Successfully saved image from '{topic}' to '{output_path}'"
        return output_path
    else:
        return f"Error: No image received from '{topic}' within {timeout} seconds"
    
    
@tool
def image_caption_generation(img_path: Optional[str]=None):
    """[Tool] Gives a caption for the image. 
    
    Args:
        img_path (str): The path to image. If not given, reading from "/tmp/ros_image.jpg"
            
    Returns:
        str: A caption of the image. 
    """
    if img_path is None:
        img_path = "/tmp/ros_image.jpg"
        
    image = PIL.Image.open(img_path).convert('RGB')

    model_name = "Salesforce/blip-image-captioning-large"
    device = "cuda" if torch.cuda.is_available() else "cpu"

    processor = BlipProcessor.from_pretrained(model_name, use_fast=True)
    model = BlipForConditionalGeneration.from_pretrained(model_name).to(device)

    inputs = processor(image, return_tensors='pt').to(device)
    output = model.generate(**inputs, max_new_tokens=20)

    caption = processor.decode(output[0], skip_special_tokens=True)

    return caption


@tool
def describe_ros_image_topic(topic: str, output_path: Optional[str]=None, timeout: float = 5.0):
    """
    A tool to subscribe to a ros2 image topic and describe what is shown in the image.
    
    Args:
        topic: ROS2 image topic to subscribe to. 
        output_path: Path where to save the image. If not given saving in "/tmp/ros_image.jpg"
        timeout: Maximum time to wait in seconds
        
    Returns:
        str: The path where the image was saved
    """ 
    print("II', here")
    # if topic is None or topic == "{}":
    #     topic = "/oakd/rgb/preview/image_raw"
    output_path = save_ros_image_to_file.func(topic, output_path, timeout) 
    print(output_path)
    return image_caption_generation.func(output_path)
    
    
# class ImageCaptionTool(BaseTool):
#     name:str = "Image captioner"
#     description:str  = "Use this tool when given the path to an image that you would like to be described. " \
#                   "It will return a simple caption describing the image."

#     def _run(self, img_path:str) -> str:
#         image = PIL.Image.open(img_path).convert('RGB')

#         model_name = "Salesforce/blip-image-captioning-large"
#         device = "cuda" if torch.cuda.is_available() else "cpu"
 
#         processor = BlipProcessor.from_pretrained(model_name)
#         model = BlipForConditionalGeneration.from_pretrained(model_name).to(device)

#         inputs = processor(image, return_tensors='pt').to(device)
#         output = model.generate(**inputs, max_new_tokens=20)

#         caption = processor.decode(output[0], skip_special_tokens=True)

#         return caption

#     def _arun(self, query:str) -> Any:
#         raise NotImplementedError("This tool does not support async")


class ObjectDetectionTool(BaseTool):
    name: str = "Object detector"
    description: str = "Use this tool when given the path to an image that you would like to detect objects. " \
                  "It will return a list of all detected objects. Each element in the list in the format: " \
                  "[x1, y1, x2, y2] class_name confidence_score."

    def _run(self, img_path:str) -> str:
        image = PIL.Image.open(img_path).convert('RGB')
        
        device = "cuda" if torch.cuda.is_available() else "cpu"

        processor = DetrImageProcessor.from_pretrained("facebook/detr-resnet-50")
        model = DetrForObjectDetection.from_pretrained("facebook/detr-resnet-50").to(device)

        inputs = processor(images=image, return_tensors="pt").to(device)
        outputs = model(**inputs)

        # convert outputs (bounding boxes and class logits) to COCO API
        # let's only keep detections with score > 0.9
        target_sizes = torch.tensor([image.size[::-1]])
        results = processor.post_process_object_detection(outputs, target_sizes=target_sizes, threshold=0.9)[0]

        detections = ""
        for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
            detections += '[{}, {}, {}, {}]'.format(int(box[0]), int(box[1]), int(box[2]), int(box[3]))
            detections += ' {}'.format(model.config.id2label[int(label)])
            detections += ' {}\n'.format(float(score))

        return detections

    def _arun(self, query: str):
        raise NotImplementedError("This tool does not support async")


@tool
def image_question_answering(question:str, img_path:Optional[str]=None):
    """[Tool] Answers a question about an image. 
    
    Raises:
        question (str): The question to be answered based on the image
        img_path (str): The path to image. If not given, reading from "/tmp/ros_image.jpg"

    Returns:
        str: The answer to the question based on the image.
    """
    if img_path is None:
        img_path = "/tmp/ros_image.jpg"
        
    image = PIL.Image.open(img_path).convert('RGB')

    model_name = "Salesforce/blip-vqa-base"
    device = "cuda" if torch.cuda.is_available() else "cpu"

    processor = AutoProcessor.from_pretrained(model_name)
    model = AutoModelForVisualQuestionAnswering.from_pretrained(model_name).to(device)

    inputs = processor(image, question, return_tensors="pt").to(device)
    output = model.generate(**inputs)

    answer = processor.decode(output[0], skip_special_tokens=True)
    return answer

    
# class ImageQuestionAnswerTool(BaseTool):
#     name:str = "Image Question Answering Tool"
#     description:str  = "Use this tool when given the path to an image and a question to be answered based on the image. " \
#                   "It will return the answer to the question about the image."
                  
#     def _run(self, img_path_question:str) -> str:
#         img_path_question_json = json.loads(img_path_question)
        
#         img_path = img_path_question_json['image_path']
#         question = img_path_question_json['question']
        
#         image = PIL.Image.open(img_path).convert('RGB')

#         model_name = "Salesforce/blip-vqa-base"
#         device = "cuda" if torch.cuda.is_available() else "cpu"
 
#         processor = AutoProcessor.from_pretrained(model_name)
#         model = AutoModelForVisualQuestionAnswering.from_pretrained(model_name).to(device)

#         inputs = processor(image, question, return_tensors="pt").to(device)
#         output = model.generate(**inputs)

#         answer = processor.decode(output[0], skip_special_tokens=True)

#         return answer             
    
#     def _arun(self, query: str):
#         raise NotImplementedError("This tool does not support async")
            
IMAGE_TOOLS = [save_ros_image_to_file, image_caption_generation, image_question_answering, describe_ros_image_topic]
def test_image_tool():   
    import sys
    sys.path.extend(['/PenguinPi_agent/ros_ws/src/penguinpi_agent/scripts']) 
    from rosa import ROSA
    from penguinpi_prompts import get_prompts
    import asyncio
    from penguinpi_llm import get_llm
    from rosa.tools.ros1 import rostopic_list
    
    tools = [save_ros_image_to_file, image_caption_generation, image_question_answering, describe_ros_image_topic, rostopic_list]    

    agent = ROSA(
        ros_version=1,   #ROS1 for PenguinPi
        llm=get_llm(streaming=False),
        tools=tools,
        blacklist=["master", "docker"],
        prompts=get_prompts(),
        verbose=True,
        accumulate_chat_history=True,
    )
    
    img_path = "/PenguinPi_agent/img.png"
    queries = [
        f' Describe what you see',
        # f'Save image from the ROS topic /oakd/rgb/preview/image_raw',
        # f'Who are in this image {img_path}',
        # f'How many animals are there {img_path}',
        # f'Give a caption for the image {img_path}'
    ]
    for q in queries:
        print(agent.invoke(q))


if __name__ == "__main__":
    test_image_tool()