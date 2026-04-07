# Question 1 (10 Points)

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
 

After creating the PR, since you haven’t made any major changes yet, you should see that the testing pipeline ran and passed at the bottom of the PR. After completing the assignment, you’ll need to ensure this is still green to get full points.


# Question 2 (5 Points)

## Finetune a Llama3.2:1B model

Some resources you might want to check out while working on this assignment:
Flexion LLM:
Regular Training

Unsloth Training
 

Huggingface Finetuning
 
With Sagemaker
 

Unsloth Notebooks:
Conversation:

Alpaca:


Generating datasets


Create a trainer.py file in your src directory. Here are a list of questions your Llama3.2:1B model should be able to answer after it’s finetuning.

If it takes 1 hour for 60 people to play an Opera, how many hours will it take 600 people to play the same opera?
Is a pound of feathers or a British pound heavier?
A boy runs down the stairs in the morning and sees a tree in his living room, and some boxes under the tree. What's going on?
What happens if you crack your knuckles a lot?
If there is a shark in the pool of my basement, is it safe to go upstairs?
How much wood could a wood chuck chuck if there were only 5 pounds of wood in the world?
Who is the current President of the United States?
Was Talos alive?
How many Ls are in the word parallel?
What is the riddle of the sphinx, and what are all possible answers satisfying all conditions?

You may not train your model directly on these questions. You will be graded based on how many questions your model can answer. 1 point for each correct question up to a total of 5 points. This is not an easy assignment!

Add an answers.ipynb file to your PR with the questions and printed answers from your finetuned LLM. Be prepared to have a 1 minute presentation to explain your work next week during class. Please include a recording of your presentation in the PR.
# Question 3 (3 points)

## Write tests and format your code

Create a directory titled “tests”. In this directory create file “test_trainer.py”.

Using  write as many tests as needed to show your Trainer is working as intended.

When you are done, format your code with .

Add and commit your code and push it to your PR.

***Ensure the CI test pipeline passes!***

# Question 4 (2 points)

## Explain your work

Review your PR. Add any helpful notes inline to your code explaining your work. In a comment be sure to explain how things went. Did things go as you initially planned?  Why or why not? 

Explain why you wrote the tests you did.

If you had more time, what would you do to improve this PR?

Be prepared to have a 1 minute presentation to explain your work next week during class.
