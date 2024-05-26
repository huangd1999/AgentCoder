# AgentCoder: Multiagent-Code Generation Framework

AgentCoder is a novel multiagent-code generation framework that leverages the power of large language models (LLMs) to enhance the effectiveness of code generation. The framework consists of three specialized agents: the programmer agent, the test designer agent, and the test executor agent. These agents collaborate to generate high-quality code snippets, design comprehensive test cases, and ensure the correctness of the generated code through an iterative feedback loop.

## Key Features

- **Multiagent Collaboration**: AgentCoder utilizes a multiagent framework where each agent specializes in a specific task, leading to improved code generation effectiveness.
- **Independent Test Case Generation**: The test designer agent generates diverse and objective test cases independently, ensuring comprehensive testing of the generated code.
- **Iterative Code Refinement**: The test executor agent executes the generated test cases against the code and provides feedback to the programmer agent for iterative code refinement.
- **Modularity and Scalability**: The modular structure of AgentCoder allows for easy integration with advanced models and future enhancements, ensuring adaptability in the evolving landscape of code generation.

## Installation

To use AgentCoder, you need to have an API key from OpenAI or other similar third-party providers.
1. Clone the AgentCoder repository:
   ```
   git clone https://github.com/your-username/AgentCoder.git
   cd AgentCoder
   git clone https://github.com/THUDM/CodeGeeX
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Add your API key in the `programmer_[humaneval/mbpp].py` and `test_designer_[humaneval/mbpp].py` files:
   ```python
   openai.api_key = 'YOUR_API_KEY'
   ```

## Usage

### Code Generation

To generate code snippets, run the following commands:
```
python programmer_[humaneval/mbpp].py
```
These scripts will generate code snippets that will be used for test case generation.

### Test Case Generation

To generate test cases, run the following command:
```
python test_designer_[humaneval/mbpp].py
```
This script will generate diverse and comprehensive test cases based on the coding requirements.

### Self-Optimization Process

To perform the self-optimization process, run the following commands:
```
python test_executor_[humaneval/mbpp].py
```
These scripts will execute the generated test cases against the code and provide feedback to the programmer agent for iterative code refinement.


## Contributions

Contributions to AgentCoder are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request on the GitHub repository.

## License

AgentCoder is released under the [MIT License](LICENSE).

## Acknowledgments

We would like to thank AIOHUB for providing funding and support for the development of AgentCoder. We also acknowledge the contributions of the open-source community and the developers of the large language models used in this project.
