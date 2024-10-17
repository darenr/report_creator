import logging
import sys

import ollama

import report_creator as rc

logging.basicConfig(level=logging.INFO)

# find the biggest local model
# sort  list of dicts by param value

if len(ollama.list()["models"]) == 0:
    logging.error("No Ollama models found!")
    sys.exit(1)


def generate_blog(model, topic):
    print(f"Generating blog plan for the topic: {topic}")

    prompt = f"""Write a long detailed technical blog in markdown on 
    
    the topic: '{topic}' 
    
    with a focus on the technical aspects of the topic. 
    
    Include code snippets, markdown tables, and code examples where appropriate.
    
    Create a conclusion of a few paragrams that summarizes the topic and the key points discussed."""

    response = ollama.generate(model=model, prompt=prompt)  # Call ollama to expand section

    blog_content = f"{response['response']}\n\n"

    with rc.ReportCreator(topic) as report:
        view = rc.Block(
            rc.Markdown(
                blog_content,
            ),
        )

        report.save(view, "blog.html")


# Example usage

if __name__ == "__main__":
    model = sorted(ollama.list()["models"], key=lambda x: x["size"], reverse=True)[0]["name"]
    logging.info(f"Using Ollama model: {model}")

    generate_blog(model, "Using ham radio SSTV to send and receive images")
