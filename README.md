# CNLP Project

## Running Experiments


### Prerequisites

1. **Create a `.env` file**  
   In the root directory of the project, create a `.env` file with the following content:
   GROQ_API_KEY=<your-groq-api-key>
   OPENAI_API_KEY=<your-openai-api-key>
   OPENAI_MODEL="gpt-4o-2024-08-06"
2. **Download the dataset**  
Download the [natural-instructions dataset](https://github.com/allenai/natural-instructions) and extract it to the root directory of the project.  


### Running the Experiments

#### Running RQ1
```bash
cd ./experiment/RQ1
python main.py
```

#### Running RQ2
```bash
cd ./experiment/RQ2
python main.py
```

#### Running RQ3
```bash
cd ./experiment/RQ3
python main.py
```
