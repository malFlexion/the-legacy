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

## Write a custom evaluation.

Some resources you might want to check out while working on this assignment:
Section 4.2 of LLMs In Production

Issues with current evaluations:


Eval libraries to consider:
DeepEval:  
Huggingface Evaluate:  

Create an evaluator and run it against a simple BERT model. Create a file named evaluator.py in the src directory. If you are feeling adventurous, try  as well!

See this example:  
Another example: .

How well did your model do? Would you choose this model for your task? Is your evaluation dataset appropriate to evaluate the task? Is the metric insightful to evaluate the task? Answer in a comment in your PR.
# Question 3 (3 points)

## Write tests and format your code

Create a directory titled “tests”. In this directory create file “test_evaluator.py”.

Using  write as many tests as needed to show your Evaluator is working as intended.

When you are done, format your code with .

Add and commit your code and push it to your PR.

***Ensure the CI test pipeline passes!***
# Question 4 (2 points)

## Explain your work

Review your PR. Add any helpful notes inline to your code explaining your work. In a comment be sure to explain how things went. Did things go as you initially planned?  Why or why not? 

Explain why you wrote the tests you did.

If you had more time, what would you do to improve this PR?
