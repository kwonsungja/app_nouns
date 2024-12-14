import gradio as gr
import pandas as pd
import random

# Load the CSV file from the provided URL
csv_url = "https://raw.githubusercontent.com/kwonsungja/app_nouns/main/regular_Nouns_real.csv"
try:
    df = pd.read_csv(csv_url)
    df.columns = df.columns.str.lower()  # 데이터프레임 열 이름을 소문자로 변환

    # 공백 제거
    df["singular"] = df["singular"].str.strip()
    df["level"] = df["level"].str.strip()
except Exception as e:
    print(f"CSV 파일을 불러오는 데 실패했습니다: {e}")
    exit()

# Count the number of items in each level
counts = df["level"].value_counts()
levels_with_counts = [
    f"{level} ({counts.get(level, 0)} items)"
    for level in ["s", "es", "ies"]
]

def initialize_user_state():
    return {
        "remaining_nouns": pd.DataFrame(),
        "current_level": None,
        "score": 0,
        "trials": 0,
        "current_index": -1,
        "level_scores": {level: {"score": 0, "trials": 0} for level in ["s", "es", "ies"]},
    }

def pluralize(noun):
    noun = noun.strip()  # 문자열의 앞뒤 공백 제거
    if noun.endswith(('s', 'ss', 'sh', 'ch', 'x', 'z', 'o')):
        return noun + 'es'
    elif noun.endswith('y') and not noun[-2] in 'aeiou':
        return noun[:-1] + 'ies'
    else:
        return noun + 's'

def filter_nouns_if_needed(level_with_count, user_state):
    level = level_with_count.split(" ")[0]
    if user_state["current_level"] != level:
        filtered_nouns = df[df["level"] == level].copy()
        if filtered_nouns.empty:
            return user_state, f"No nouns available for the Level: {level}. Please select a different level."
        user_state["remaining_nouns"] = filtered_nouns
        user_state["current_level"] = level
        user_state["score"] = 0
        user_state["trials"] = 0
        user_state["current_index"] = -1
        return user_state, f"Level {level} selected. Click 'Show the Noun' to start!"
    return user_state, None

def show_next_noun(level_with_count, user_state):
    user_state, feedback = filter_nouns_if_needed(level_with_count, user_state)
    if user_state["remaining_nouns"].empty:
        return user_state, feedback or "All nouns have been answered correctly. Great job!", ""
    user_state["current_index"] = random.randint(0, len(user_state["remaining_nouns"]) - 1)
    selected_noun = user_state["remaining_nouns"].iloc[user_state["current_index"]]
    return user_state, f"What's the plural form of '{selected_noun['singular']}'?", ""

def check_plural(user_plural, user_state):
    if user_state["remaining_nouns"].empty:
        return user_state, f"All nouns have been answered correctly. Great job! (Score: {user_state['score']}/{user_state['trials']})"

    index = user_state["current_index"]
    if index == -1:
        return user_state, f"Please click 'Show the Noun' first. (Score: {user_state['score']}/{user_state['trials']})"

    noun_data = user_state["remaining_nouns"].iloc[index]
    singular = noun_data["singular"]
    correct_plural = pluralize(singular)

    user_state["trials"] += 1
    user_state["level_scores"][user_state["current_level"]]["trials"] += 1

    # 사용자 입력과 정답 비교 시 공백 제거
    if user_plural.strip().lower() == correct_plural.strip().lower():
        user_state["score"] += 1
        user_state["level_scores"][user_state["current_level"]]["score"] += 1
        feedback = f"✅ Correct! '{correct_plural}' is the plural form of '{singular}'. Click 'Show the Noun' to continue."
        user_state["remaining_nouns"] = user_state["remaining_nouns"].drop(user_state["remaining_nouns"].index[index])
    else:
        feedback = f"❌ Incorrect. The correct plural form is '{correct_plural}' for '{singular}'. It will appear again."

    if user_state["remaining_nouns"].empty:
        feedback += f"\n🎉 All nouns have been answered correctly. Great job! (Score: {user_state['score']}/{user_state['trials']})"

    return user_state, f"{feedback} (Score: {user_state['score']}/{user_state['trials']})"

def display_total_score(user_state):
    total_score = ", ".join(
        f"{level}({user_state['level_scores'][level]['score']}/{user_state['level_scores'][level]['trials']})"
        for level in ["s", "es", "ies"]
    )
    return total_score

with gr.Blocks() as app:
    gr.Markdown("# NounSmart: Practice regular Plural Nouns")
    gr.Markdown("""
    ## How to Use the App
    1. **Follow the steps from Step 1 to Step 4.**
    2. **Click 'Show Report' to view overall feedback across all levels.**
    """)

    level_dropdown = gr.Dropdown(
        label="Step 1. Select a Level to start.",
        choices=levels_with_counts,
        value=levels_with_counts[0],
        interactive=True
    )

    show_button = gr.Button("Step 2. Show the Noun")
    noun_display = gr.Textbox(label="Singular Noun", value="Select a level to start", interactive=False)

    plural_input = gr.Textbox(label="Step 3. Type Your answer.", placeholder="Type your answer here")

    submit_button = gr.Button("Step 4. See the Answer and Feedback")
    feedback_display = gr.Textbox(label="Feedback and Score", interactive=False)

    total_score_button = gr.Button("Show Report")
    total_score_display = gr.Textbox(label="Total Score by Levels", interactive=False)

    state = gr.State(initialize_user_state())

    show_button.click(fn=show_next_noun, inputs=[level_dropdown, state], outputs=[state, noun_display, plural_input])
    submit_button.click(fn=check_plural, inputs=[plural_input, state], outputs=[state, feedback_display])
    total_score_button.click(fn=display_total_score, inputs=state, outputs=total_score_display)

app.launch()
