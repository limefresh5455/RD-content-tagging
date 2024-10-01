import re
import difflib
import pandas as pd
from openai import OpenAI
from response_model import TopicSubtopic
client = OpenAI()

topics_df = pd.read_csv("topics.csv")
topic_subtopic_pairs = [f"Topic: {topic}, SubTopic: {subtopic}" for topic, subtopic in zip(topics_df['Topic'], topics_df['Subtopic'])]
topic_subtopic_pairs_str = "\n".join(topic_subtopic_pairs)

def generate(content : str) -> str:

    # Create a list of all possible topic-subtopic combinations
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"""
                                            You are working as a classifier to categorize content using the provided list of topics and subtopics.

                                            Possible topics and subtopics:

                                            {topic_subtopic_pairs_str}

                                            **Important**: If the content cannot be classified into the provided list, provide the closest topic and subtopic from the list above. 
                            
                                            - If there are multiple close matches, provide the closest topic and subtopic combination.
                                            - Your response should be formatted exactly as: "Topic: topic, SubTopic: subtopic"
                                            - Use only the topics and subtopics given in the provided list above. Do not introduce any new topics or subtopics.
                                            """
            },
            {"role": "user", "content": content}
        ],
        max_tokens=50,
        temperature=0.05
    )
    categories = str(response.choices[0].message.content)
    if categories not in topic_subtopic_pairs_str:
        closest_match = difflib.get_close_matches(categories, topic_subtopic_pairs, n=2, cutoff=0.6)#difflib.get_close_matches function uses a sequence similarity algorithm to find the closest matches
        if closest_match:
            return closest_match[0]

    topic_subtopic = get_topic_subtopic(categories)
    return TopicSubtopic(**topic_subtopic)

#_________________________generate Summary for pdf__________________________________________
def generate_summary(content):
    response =client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": """
                                            You are an expert summarizer. Summarize the given content concisely and clearly.
                                            """
            },
            {"role": "user", "content": content}
        ],
        max_tokens=250,
        temperature=0.1
    )
    summary = str(response.choices[0].message.content)
    return summary

def get_topic_subtopic(topic_subtopic_str : str):
    match = re.search(r'Topic:\s*(.*?),\s*SubTopic:\s*(.*)', topic_subtopic_str)
    if match:
        result = {
            "topic": match.group(1).strip('<>'),
            "subtopic": match.group(2).strip('<>')
        }
    return result