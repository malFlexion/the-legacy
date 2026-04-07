# Question 1 (3 points)

## Create a PR to the class’s GitHub repo.

Do each step by running the accompanying command in a terminal.

If you haven’t already, install git and uv.
 
 

You will need to be added as a collaborator to the repo if you haven’t been already. Please send a message to the instructor with your Github tag to make sure you have access. (Hint: if your Github tag is in your Slack bio then you are likely already added.)

Clone the repo: 
```
git clone git@github.com:flexion/llm-class-2026-winter-cohort.git

Change Directory:
	cd llm-class-2026-winter-cohort

Create a branch and move into it: 
(Please change <branch-name> to your name and the assignment number. e.g. matt-sharp-assignment-1 or matt_sharp_1)
	git checkout -b <branch-name>
```

Make a change to the branch (maybe add a CLAUDE.md file).

(optional but highly recommended) Install the pre-commits:
```
	uvx pre-commit install
```

*Note: this will ensure tests and linters run before every `git commit` which will save you a lot of time debugging.*

Add your changes.
```
git add .
```

Commit your changes
```
git commit -m “My first commit”

Push this to Github
	git push origin <branch-name>
```

**Important!** Submit a pull request. Git will likely give you a link to create this when you make your first push, otherwise you can find your branch in the repo on Github and create a PR. 

# Question 2 (5 points) 

## Build a Basic Tokenizer

## First: Download a Dataset

Feel free to choose any dataset you want, but I’ll recommend these two:

Proposal Writing dataset (Flexion specific):
 
Note, the easiest way to work with this data will be to download it as .txt or .md.  Ultimately, since this is columnar data, you may want to first copy it to a Google sheet and download it as a .csv. Make sure you are on the Export Copy tab when you download it.


StarWars scripts (for fun):
 
If you are new to HuggingFace and would like to use the StarWards dataset, the easiest way is to go to the “Files and Versions” tab, then select the Download file button.

You can also download it via git-lfs or by using the huggingface dataset sdk if you are adventurous.  
## Ignore unwanted files

If your dataset is in your repo, please add it to your .gitignore file at the base of the repo to keep your git history clean. The dataset is a large file that is best to ignore and keep out of source control. Please add anything else that should be ignored to your .gitignore if it isn’t already.  
## Next, implement tokenization.

Create a file in the src directory named tokenizer.py.

To pass this assignment, you just need to copy/paste the below code, and get it running with the dataset you downloaded above.


# Question 3 (2 points)

Write tests and format your code
In the tests directory create a file named test_tokenizer.py.

Using  write as many tests as needed to show your Tokenizer is working as intended. 
**Hint**: write fixtures for any datasets you may be using. Mock any api calls or models used. 
**Note**: the CI pipeline will fail if there is less than 80% test coverage.

When you are done, format your code with .
## Update and Submit your PR.

```
	git add .
	git commit -m “Creating a tokenizer”
	git push origin <branch-name>

Ensure the CI test pipeline passes!
```

| # Build Vocab
all_tokens = sorted(list(set(preprocessed)))
all_tokens.extend(["<|endoftext|>", "<|unk|>"])
vocab = {token:integer for integer,token in enumerate(all_tokens)}
print(len(vocab.items()))

# Tokenize
class SimpleTokenizer:
    def __init__(self, vocab):
        self.str_to_int = vocab
        self.int_to_str = { i:s for s,i in vocab.items()}

    def encode(self, text):
        preprocessed = re.split(r'([,.:;?_!"()\']|--|\s)', text)
        preprocessed = [
            item.strip() for item in preprocessed if item.strip()
        ]
        preprocessed = [item if item in self.str_to_int 
            else "<|unk|>" for item in preprocessed]
        ids = [self.str_to_int[s] for s in preprocessed]
        return ids

    def decode(self, ids):
        text = " ".join([self.int_to_str[i] for i in ids])
        text = re.sub(r'\s+([,.:;?!"()\'])', r'\1', text)
        return text |
| --- |
