# CNLP Project


## Experiments


### Prerequisites

1. **Create a `.env` file**  
   In the root directory of the project, create a `.env` file with the following content:<br>
   GROQ_API_KEY=your-groq-api-key<br>
   OPENAI_API_KEY=your-openai-api-key<br>
   OPENAI_MODEL="gpt-4o-2024-08-06"<br>
2. **Please specify the Python version as Python 3.11.8**
3. **Download the dataset**  
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


## Other Explanations
The content of the 'src' directory is identical to that of 'experiment/RQ3/src', allowing you to directly review the Linter content.
