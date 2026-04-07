# Question 1 (2 Points)

### Create a Pull Request and Create a Plan

Notes: To do it off the latest main branch use the following commands. You can also change main to another branch if you want to reuse previous work.
git checkout main
git pull
git checkout -b <branch>
<edit some file>
git add <file>
git commit -m “Homework assignment X”
git push origin <branch>
<Go to Github and be sure to create the PR>

Create a comment for your PR with a plan of action. Your plan of action should encompass how you plan to finish each of the other questions in this homework assignment. Do not edit this comment and it should be the first comment in the PR history.

Abraham Lincoln is often quoted as saying, “If I had eight hours to chop down a tree, I'd spend the first six hours sharpening my axe”. You will be graded based on the preparation and research you put into it. Your plan of action should be a short essay.

In your plan of action explain various approaches that you could take. Talk about their potential pros and cons. What alternatives did you consider to these decisions?

If it helps to think in these terms, this is essentially a mini-ADR (Architectural Decision Record).
Resource:
 
Template:
 
# Question 2 (5 Points)

## Run a model on a GPU in Sagemaker.

Some resources:
 


Get the following basic code to run a text generation pipeline with HuggingFace’s transformers on a Sagemaker GPU instance.
```
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
```

```
# Load tokenizer and model
model_id = "meta-llama/Llama-3.2-1B"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id, device_map="auto")
```

```
# Create a text generation pipeline
generator = pipeline("text-generation", model=model, tokenizer=tokenizer)
```

```
# Generate text
prompt = "Once upon a time"
output = generator(prompt, max_new_tokens=50, do_sample=True, temperature=0.7)
```

```
# Print result
print(output[0]['generated_text'])
```

```
Once you get the above code to work, use a larger model.  What’s the biggest Llama model you could get to run on the GPU you chose?  While it’s running, run nvidia-smi in a terminal and take a screenshot of the GPU at work.
```

***Important! Be sure to turn off your Sagemaker Space.***

# Question 3 (10 points)

## Explore Sagemaker. 

In a comment, answer the following questions:

What’s the difference between Sagemaker and Sagemaker AI?
What is Sagemaker Studio?
What is Sagemaker Unified Studio?
What is a Sagemaker AI domain?
What is a Sagemaker AI space?
What is a Sagemaker AI notebook?
What is the difference between Jupyterlab and Code Editor space?
How does Bedrock relate to Sagemaker?
What is MLFlow? In the context of Sagemaker?
Will your GPU instance shut off on its own? If not, how do you ensure it is turned off?
# Question 4 (3 points)

## Explain your work

In a comment be sure to explain how things went. Did things go as you initially planned?  Why or why not? 

Add any additional insights you gained from exploring Sagemaker. Any interesting facts you stumbled upon?  Add any screenshots of your exploration that might help me understand what you did.

If you had more time, what more would you do?

Ensure any resources you used have been turned off.
