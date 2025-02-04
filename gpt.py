import json
import boto3
import os
import logging
from botocore.exceptions import ClientError
import PyPDF2
import openai

# Logging Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# GPT-4 Configuration
OPENAI_API_KEY = ""

s3 = boto3.client(
    "s3",
    aws_access_key_id="",
    aws_secret_access_key="",
    region_name=""
)

# Static Examples
EXAMPLES = [
    {"criterion": "LLM Experience and Knowledge",
     "example": "Built a chatbot for multiple PDFs and videos using LangChain, NLTK, and SpaCy, and deployed it via Streamlit.",
     "score": 7,
     "explanation": "Demonstrates advanced proficiency in working with LLMs, integrating them into applications, and deploying solutions effectively."},

    {"criterion": "LLM Experience and Knowledge",
     "example": "Made a project on Retrieval-Augmented Generation (RAG) development and Large Language Models (LLMs).",
     "score": 9,
     "explanation": "Shows theoretical knowledge and interest in state-of-the-art techniques but lacks practical project implementation."},

    {"criterion": "LLM Experience and Knowledge",
     "example": "Participated in academic research exploring applications of LLMs in education.",
     "score": 5,
     "explanation": "Limited scope of application and lacks substantial implementation experience."},

    {"criterion": "LLM Experience and Knowledge",
     "example": "Conducted a basic study of ChatGPT's capabilities for answering domain-specific queries.",
     "score": 2,
     "explanation": "Minimal hands-on work, focused more on exploration than implementation or deployment."},

    {"criterion": "Good Institute (IIT or NIT)",
     "example": "Student at one of the old IITs ",
     "score": 10,
     "explanation": "IIT is among the top institutions in India, reflecting strong academic credentials and a competitive environment."},

    {"criterion": "Good Institute (IIT or NIT)",
     "example": "Graduate from NIT Suratkal in Computer Science.",
     "score": 8,
     "explanation": "NIT Suratkal is a prestigious institution with a strong focus on technical education and research."},

    {"criterion": "Good Institute (IIT or NIT)",
     "example": "Student at a private engineering college with good regional reputation.",
     "score": 6,
     "explanation": "While the institution is not IIT/NIT, it is still reputable in a regional context."},

    {"criterion": "Generative AI Experience",
     "example": "Developed a virtual try-on system using GANs, PyTorch, and OpenCV.",
     "score": 10,
     "explanation": "Demonstrates expertise in Generative AI, leveraging advanced techniques for real-world applications."},

    {"criterion": "Generative AI Experience",
     "example": "Explored GAN-based image generation as part of an academic project.",
     "score": 7,
     "explanation": "Theoretical knowledge with limited practical experience in implementing and deploying systems."},

    {"criterion": "Generative AI Experience",
     "example": "Built a simple image generator using a pre-trained GAN model.",
     "score": 5,
     "explanation": "Basic implementation using pre-trained models without significant customization or original contributions."},

    {"criterion": "Generative AI Experience",
     "example": "Read research papers on diffusion models and GANs.",
     "score": 3, 
     "explanation": "Shows interest and theoretical knowledge but lacks hands-on experience."},

    {"criterion": "Leadership and Teamwork", 
     "example": "Led a team for a fraud detection model.", 
     "score": 8, 
     "explanation": "Proven leadership and teamwork skills."},

    {"criterion": "Leadership and Teamwork", 
     "example": "Organized a hackathon for 200 participants.", 
     "score": 5, 
     "explanation": "Moderate leadership experience."}
]

def extract_text_from_pdf(file_path):
    """
    Extract text content from PDF using PyPDF2.
    Handles both regular text and table content.
    """
    try:
        text_content = []
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text_content.append(page.extract_text())
        
        # Join all pages with proper spacing
        return '\n'.join(text_content)
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        raise

def list_files_in_folder(bucket_name, folder_path):
    """List all PDF files in the specified S3 folder."""
    try:
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=folder_path)
        if "Contents" in response:
            return [obj["Key"] for obj in response["Contents"] if obj["Key"].endswith(".pdf")]
        return []
    except ClientError as e:
        logger.error(f"Error listing files in S3 bucket: {e}")
        return []

def download_resume_from_s3(bucket_name, resume_key, download_path="/tmp"):
    """Download resume from S3 to local temporary storage."""
    local_file_path = f"{download_path}/{resume_key.split('/')[-1]}"
    try:
        s3.download_file(bucket_name, resume_key, local_file_path)
        return local_file_path
    except ClientError as e:
        logger.error(f"Error downloading file {resume_key}: {e}")
        raise

def check_qualifying_criteria_with_gpt(resume_text):
    """
    Use GPT-4 to evaluate if the candidate meets qualifying criteria.
    """
    prompt = """
    Analyze the following resume and determine if the candidate meets these criteria:
    1. Has at least 2 years of relevant experience
    2. Has worked at a Tier 1 company (Google, Amazon, Microsoft, Meta, Apple)

    Please provide a clear YES/NO answer with a brief explanation.

    Resume Text:
    {resume_text}
    """
    
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)        
        response = client.chat.completions.create(  # Updated method
        model="gpt-4o",
        messages=[
                {"role": "system", "content": "You are an HR assistant evaluating resumes."},
                {"role": "user", "content": prompt.format(resume_text=resume_text)}
            ],
        temperature=0.7
        )
        
        result = response.choices[0].message.content  # Updated attribute access
        qualified = "YES" in result.split('\n')[0].upper()
        return qualified, result
    except Exception as e:
        logger.error(f"Error in GPT qualification check: {e}")
        raise

def evaluate_resume_with_gpt(resume_text, criterion, weight):
    """
    Evaluate resume against specific criterion using GPT-4.
    """
    examples_subset = [ex for ex in EXAMPLES if ex['criterion'] == criterion][:3]
    examples_text = "\n".join(
        f"Example {i+1}:\nCriterion: {ex['criterion']}\nResume: {ex['example']}\nScore: {ex['score']}\nExplanation: {ex['explanation']}"
        for i, ex in enumerate(examples_subset)
    )

    prompt = f"""
    You are an expert HR assistant evaluating resumes. Below is a candidate's resume and the criterion for evaluation:

    Criterion: {criterion}
    Weight: {weight}

    ### Candidate's Resume:
    {resume_text}

    ### Examples of Evaluation:
    {examples_text}

    Using the examples, evaluate the resume:
    - Provide a single score (1-10).
    - Provide a justification for the score.
    """
    
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)  # And here
        response = client.chat.completions.create(  # Updated method
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an HR assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content  # Updated attribute access
    except Exception as e:
        logger.error(f"Error in GPT evaluation: {e}")
        raise

def process_resume(bucket_name, resume_key):
    """Process a single resume through the evaluation pipeline."""
    try:
        # Download and extract text from PDF
        local_file_path = download_resume_from_s3(bucket_name, resume_key)
        resume_text = extract_text_from_pdf(local_file_path)
        
        # Check qualifying criteria
        qualified, qualification_details = check_qualifying_criteria_with_gpt(resume_text)
        
        if qualified:
            # Evaluate against all criteria
            evaluations = {}
            for criterion in set(ex["criterion"] for ex in EXAMPLES):
                weight = 10  # Default weight
                result = evaluate_resume_with_gpt(resume_text, criterion, weight)
                evaluations[criterion] = result
            
            return {
                "resume_key": resume_key,
                "status": "Qualified",
                "qualification_details": qualification_details,
                "evaluations": evaluations,
                "resume_text": resume_text
            }
        else:
            return {
                "resume_key": resume_key,
                "status": "Not Qualified",
                "qualification_details": qualification_details
            }
            
    except Exception as e:
        logger.error(f"Error processing resume {resume_key}: {e}")
        return {"resume_key": resume_key, "error": str(e)}
    
def main():
    """Main function for local execution"""
    try:
        # Configuration - modify these as needed
        bucket_name = "hm-video-audio-bucket"
        folder_path = "resumes/77KFnlghWUnWhYG/"  # Example folder path
        
        # Get list of PDF files in S3 folder
        resume_keys = list_files_in_folder(bucket_name, folder_path)
        if not resume_keys:
            print(f"No resumes found in {bucket_name}/{folder_path}")
            return

        # Process all resumes
        results = []
        for resume_key in resume_keys:
            print(f"\nProcessing {resume_key}...")
            result = process_resume(bucket_name, resume_key)
            results.append(result)
            print(json.dumps(result, indent=2))

        # Save final results
        with open("results.json", "w") as f:
            json.dump(results, f, indent=2)
            
        print("\nProcessing complete. Results saved to results.json")

    except Exception as e:
        logger.error(f"Error occurred: {e}")
        raise

if __name__ == "__main__":
    # Create temporary directory if it doesn't exist
    os.makedirs("./tmp", exist_ok=True)
    main()




# AWS CODE --------------------------------------------------------------------------------------

# import json
# import boto3
# import time
# import os
# import logging
# from botocore.exceptions import ClientError
# import PyPDF2
# import openai  

# # Logging Configuration
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # GPT-4 Configuration
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# openai.api_key = OPENAI_API_KEY

# # OpenAI GPT-4 Pricing
# PROMPT_COST_PER_1000_TOKENS = 0.0025
# COMPLETION_COST_PER_1000_TOKENS = 0.01

# s3 = boto3.client("s3")

# # Static Examples
# EXAMPLES = [
#     {"criterion": "LLM Experience and Knowledge",
#      "example": "Built a chatbot for multiple PDFs and videos using LangChain, NLTK, and SpaCy, and deployed it via Streamlit.",
#      "score": 7,
#      "explanation": "Demonstrates advanced proficiency in working with LLMs, integrating them into applications, and deploying solutions effectively."},

#     {"criterion": "LLM Experience and Knowledge",
#      "example": "Made a project on Retrieval-Augmented Generation (RAG) development and Large Language Models (LLMs).",
#      "score": 9,
#      "explanation": "Shows theoretical knowledge and interest in state-of-the-art techniques but lacks practical project implementation."},

#     {"criterion": "LLM Experience and Knowledge",
#      "example": "Participated in academic research exploring applications of LLMs in education.",
#      "score": 5,
#      "explanation": "Limited scope of application and lacks substantial implementation experience."},

#     {"criterion": "LLM Experience and Knowledge",
#      "example": "Conducted a basic study of ChatGPT's capabilities for answering domain-specific queries.",
#      "score": 2,
#      "explanation": "Minimal hands-on work, focused more on exploration than implementation or deployment."},

#     {"criterion": "Good Institute (IIT or NIT)",
#      "example": "Student at one of the old IITs ",
#      "score": 10,
#      "explanation": "IIT is among the top institutions in India, reflecting strong academic credentials and a competitive environment."},

#     {"criterion": "Good Institute (IIT or NIT)",
#      "example": "Graduate from NIT Suratkal in Computer Science.",
#      "score": 8,
#      "explanation": "NIT Suratkal is a prestigious institution with a strong focus on technical education and research."},

#     {"criterion": "Good Institute (IIT or NIT)",
#      "example": "Student at a private engineering college with good regional reputation.",
#      "score": 6,
#      "explanation": "While the institution is not IIT/NIT, it is still reputable in a regional context."},

#     {"criterion": "Generative AI Experience",
#      "example": "Developed a virtual try-on system using GANs, PyTorch, and OpenCV.",
#      "score": 10,
#      "explanation": "Demonstrates expertise in Generative AI, leveraging advanced techniques for real-world applications."},

#     {"criterion": "Generative AI Experience",
#      "example": "Explored GAN-based image generation as part of an academic project.",
#      "score": 7,
#      "explanation": "Theoretical knowledge with limited practical experience in implementing and deploying systems."},

#     {"criterion": "Generative AI Experience",
#      "example": "Built a simple image generator using a pre-trained GAN model.",
#      "score": 5,
#      "explanation": "Basic implementation using pre-trained models without significant customization or original contributions."},

#     {"criterion": "Generative AI Experience",
#      "example": "Read research papers on diffusion models and GANs.",
#      "score": 3, 
#      "explanation": "Shows interest and theoretical knowledge but lacks hands-on experience."},

#     {"criterion": "Leadership and Teamwork", 
#      "example": "Led a team for a fraud detection model.", 
#      "score": 8, 
#      "explanation": "Proven leadership and teamwork skills."},

#     {"criterion": "Leadership and Teamwork", 
#      "example": "Organized a hackathon for 200 participants.", 
#      "score": 5, 
#      "explanation": "Moderate leadership experience."}
# ]

# def extract_text_from_pdf(file_path):
#     """
#     Extract text content from PDF using PyPDF2.
#     Handles both regular text and table content.
#     """
#     try:
#         text_content = []
#         with open(file_path, 'rb') as file:
#             pdf_reader = PyPDF2.PdfReader(file)
            
#             for page_num in range(len(pdf_reader.pages)):
#                 page = pdf_reader.pages[page_num]
#                 text_content.append(page.extract_text())
        
#         # Join all pages with proper spacing
#         return '\n'.join(text_content)
#     except Exception as e:
#         logger.error(f"Error extracting text from PDF: {e}")
#         raise

# def list_files_in_folder(bucket_name, folder_path):
#     """List all PDF files in the specified S3 folder."""
#     try:
#         response = s3.list_objects_v2(Bucket=bucket_name, Prefix=folder_path)
#         if "Contents" in response:
#             return [obj["Key"] for obj in response["Contents"] if obj["Key"].endswith(".pdf")]
#         return []
#     except ClientError as e:
#         logger.error(f"Error listing files in S3 bucket: {e}")
#         return []

# def download_resume_from_s3(bucket_name, resume_key, download_path="/tmp"):
#     """Download resume from S3 to local temporary storage."""
#     local_file_path = f"{download_path}/{resume_key.split('/')[-1]}"
#     try:
#         s3.download_file(bucket_name, resume_key, local_file_path)
#         return local_file_path
#     except ClientError as e:
#         logger.error(f"Error downloading file {resume_key}: {e}")
#         raise

# def check_qualifying_criteria_with_gpt(resume_text):
#     """
#     Use GPT-4 to evaluate if the candidate meets qualifying criteria.
#     """
#     prompt = """
#     Analyze the following resume and determine if the candidate meets these criteria:
#     1. Has at least 2 years of relevant experience
#     2. Has worked at a Tier 1 company (Google, Amazon, Microsoft, Meta, Apple)

#     Please provide a clear YES/NO answer with a brief explanation.

#     Resume Text:
#     {resume_text}
#     """
    
#     try:
#         response = openai.ChatCompletion.create(
#             model="gpt-4o",
#             messages=[
#                 {"role": "system", "content": "You are an HR assistant evaluating resumes."},
#                 {"role": "user", "content": prompt.format(resume_text=resume_text)}
#             ],
#             temperature=0.7
#         )
        
#         result = response["choices"][0]["message"]["content"]
#         # Simple heuristic: if "YES" appears in the first line of the response
#         qualified = "YES" in result.split('\n')[0].upper()
#         return qualified, result
#     except Exception as e:
#         logger.error(f"Error in GPT qualification check: {e}")
#         raise

# def evaluate_resume_with_gpt(resume_text, criterion, weight):
#     """
#     Evaluate resume against specific criterion using GPT-4.
#     """
#     examples_subset = [ex for ex in EXAMPLES if ex['criterion'] == criterion][:3]
#     examples_text = "\n".join(
#         f"Example {i+1}:\nCriterion: {ex['criterion']}\nResume: {ex['example']}\nScore: {ex['score']}\nExplanation: {ex['explanation']}"
#         for i, ex in enumerate(examples_subset)
#     )

#     prompt = f"""
#     You are an expert HR assistant evaluating resumes. Below is a candidate's resume and the criterion for evaluation:

#     Criterion: {criterion}
#     Weight: {weight}

#     ### Candidate's Resume:
#     {resume_text}

#     ### Examples of Evaluation:
#     {examples_text}

#     Using the examples, evaluate the resume:
#     - Provide a single score (1-10).
#     - Provide a justification for the score.
#     """
    
#     try:
#         response = openai.ChatCompletion.create(
#             model="gpt-4o",
#             messages=[
#                 {"role": "system", "content": "You are an HR assistant."},
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0.7
#         )
#         return response["choices"][0]["message"]["content"]
#     except Exception as e:
#         logger.error(f"Error in GPT evaluation: {e}")
#         raise

# def process_resume(bucket_name, resume_key):
#     """Process a single resume through the evaluation pipeline."""
#     try:
#         # Download and extract text from PDF
#         local_file_path = download_resume_from_s3(bucket_name, resume_key)
#         resume_text = extract_text_from_pdf(local_file_path)
        
#         # Check qualifying criteria
#         qualified, qualification_details = check_qualifying_criteria_with_gpt(resume_text)
        
#         if qualified:
#             # Evaluate against all criteria
#             evaluations = {}
#             for criterion in set(ex["criterion"] for ex in EXAMPLES):
#                 weight = 10  # Default weight
#                 result = evaluate_resume_with_gpt(resume_text, criterion, weight)
#                 evaluations[criterion] = result
            
#             return {
#                 "resume_key": resume_key,
#                 "status": "Qualified",
#                 "qualification_details": qualification_details,
#                 "evaluations": evaluations,
#                 "resume_text": resume_text
#             }
#         else:
#             return {
#                 "resume_key": resume_key,
#                 "status": "Not Qualified",
#                 "qualification_details": qualification_details
#             }
            
#     except Exception as e:
#         logger.error(f"Error processing resume {resume_key}: {e}")
#         return {"resume_key": resume_key, "error": str(e)}

# def lambda_handler(event, context):
#     """AWS Lambda handler function."""
#     try:
#         body = json.loads(event['body'])

#         bucket_name = "hm-video-audio-bucket"
#         folder_path = body.get("folder_path")

#         if not folder_path:
#             raise Exception("No folder path provided.")

#         # Replace backslashes with forward slashes
#         folder_path = folder_path.replace("\\", "/")

#         # Get list of PDF files
#         resume_keys = list_files_in_folder(bucket_name, folder_path)
#         if not resume_keys:
#             raise Exception(f"No resumes found in the specified folder: {folder_path}")
        
#         # Process all resumes
#         results = [process_resume(bucket_name, resume_key) for resume_key in resume_keys]
        
#         return {
#             "statusCode": 200,
#             "body": json.dumps({"results": results}, indent=4)
#         }
#     except Exception as e:
#         logger.error(f"Error occurred: {e}")
#         return {
#             "statusCode": 500,
#             "body": json.dumps({"error": str(e)})
#         }



    
