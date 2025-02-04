# RealtyAI - Resume Analysis and Scoring System

## Repository Structure
- `resume_repository/`: Contains sample resumes used for testing
- `BERTScorer Evaluation.docx`: Documentation of model's reasoning capability testing
- `Cost Cutting Strategy.docx`: Strategic planning document for project optimization
- `Resume Scoring.xlsx`: Comparative performance analysis using multiple APIs (GPT4, GPT-1, Deepseek)
- `dockerfile`: Configuration for AWS deployment
- `gpt.py`: Main model implementation and AWS Lambda function code (included as comment)
- `requirements.txt`: Required Python dependencies
- `results.json`: Latest model output results

## Setup Instructions
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run locally using any IDE with Python support

## AWS Deployment
The system is configured for AWS deployment using Docker. The Lambda function code is included in gpt.py. The deployment of the lambda function is pending.

## Dependencies
See requirements.txt for a complete list of required packages.

## Usage
1. Ensure all dependencies are installed
2. Run gpt.py for local execution
3. Follow AWS deployment instructions for cloud implementation

## Performance
Detailed performance metrics and comparisons can be found in Resume Scoring.xlsx
