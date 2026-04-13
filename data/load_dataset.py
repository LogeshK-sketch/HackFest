import pandas as pd

def load_and_clean_questions(csv_path: str) -> list[dict]:
    """
    Dataset source: Kaggle – Engineering Aptitude Test Questions
    Author: Keith Zidan Dsouza

    Loads the Kaggle aptitude CSV, cleans it, and returns a list
    of dicts ready for DB insertion.

    Steps performed:
    1. Read CSV with pandas
    2. Rename columns to snake_case
    3. Drop rows where any of these columns is null or empty string
    4. Drop duplicate rows based on 'question_text' (keep first)
    5. Strip leading/trailing whitespace from all string columns
    6. Normalize correct_answer
    7. Assign difficulty based on row index position in the cleaned dataframe
    8. Assign category using keyword detection on question_text (case-insensitive)
    9. Return list of dicts with keys matching Question model fields
    10. Print summary
    """
    print(f"Loading data from {csv_path}...")
    df = pd.read_csv(csv_path, sep = ';')
    total_rows_read = len(df)
    
    # 2. Rename columns
    df = df.rename(columns={
        'Question': 'question_text',
        'Option A': 'option_a',
        'Option B': 'option_b',
        'Option C': 'option_c',
        'Option D': 'option_d',
        'Answer': 'correct_answer'
    })
    
    # 3. Drop rows where any column is null or empty string
    required_cols = ['question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer']
    df = df.dropna(subset=required_cols)
    for col in required_cols:
        df = df[df[col] != '']
        
    # 4. Drop duplicate rows based on 'question_text' (keep first)
    df = df.drop_duplicates(subset=['question_text'], keep='first')
    
    # 5. Strip whitespace
    for col in df.select_dtypes(['object', 'string']).columns:
        df[col] = df[col].astype(str).str.strip()
        
    # 6. Normalize correct_answer
    rows_before = len(df)
    df['correct_answer'] = df['correct_answer'].str[0].str.upper()
    df = df[df['correct_answer'].isin(['A', 'B', 'C', 'D'])]
    dropped_at_normalization = rows_before - len(df)
    print(f"Rows dropped due to invalid answer choices: {dropped_at_normalization}")
    
    # Reset index for position-based logic
    df = df.reset_index(drop=True)
    
    # 7. Assign difficulty
    total_cleaned = len(df)
    third = total_cleaned // 3
    
    def get_difficulty(idx):
        if idx < third:
            return 'easy'
        elif idx < 2 * third:
            return 'medium'
        else:
            return 'hard'
            
    df['difficulty'] = [get_difficulty(i) for i in range(total_cleaned)]
    
    # 8. Assign category using keyword detection
    numerical_keywords = ['ratio', 'percentage', 'profit', 'loss', 'interest', 'time', 'speed', 'work', 'average', 'number']
    logical_keywords = ['series', 'pattern', 'sequence', 'analogy', 'odd one', 'coding', 'direction', 'ranking', 'syllogism', 'blood relation']
    verbal_keywords = ['synonym', 'antonym', 'grammar', 'vocabulary', 'sentence', 'passage', 'comprehension', 'fill in', 'idiom']
    
    def get_category(q_text):
        q_text_lower = q_text.lower()
        if any(kw in q_text_lower for kw in numerical_keywords):
            return 'numerical'
        if any(kw in q_text_lower for kw in logical_keywords):
            return 'logical'
        if any(kw in q_text_lower for kw in verbal_keywords):
            return 'verbal'
        return 'aptitude'
        
    df['category'] = df['question_text'].apply(get_category)
    
    # 9. Return list of dicts
    result = df.to_dict(orient='records')
    
    # 10. Print summary
    print("--- Summary ---")
    print(f"Total rows read: {total_rows_read}")
    print(f"Rows after cleaning: {total_cleaned}")
    print(f"Total rows dropped: {total_rows_read - total_cleaned}")
    print(f"Category distribution:\n{df['category'].value_counts().to_string()}")
    print(f"Difficulty distribution:\n{df['difficulty'].value_counts().to_string()}")
    print("---------------")
    
    return result

def validate_question(row: dict) -> tuple[bool, str]:
    """
    Validates a single question dict before DB insertion.
    Returns (True, '') if valid.
    Returns (False, reason_string) if invalid.

    Validation rules:
    - question_text length: 10 to 2000 characters
    - option_a/b/c/d: each 1 to 500 characters, not empty
    - correct_answer: exactly one of ['A','B','C','D']
    - category: one of ['aptitude','logical','verbal','numerical']
    - difficulty: one of ['easy','medium','hard']
    """
    text = row.get('question_text', '')
    if not isinstance(text, str) or len(text) < 10 or len(text) > 2000:
        return False, f"Invalid question_text length: {len(text) if isinstance(text, str) else 'Not a string'}"
        
    for opt in ['option_a', 'option_b', 'option_c', 'option_d']:
        val = row.get(opt, '')
        if not isinstance(val, str) or len(val) < 1 or len(val) > 500:
            return False, f"Invalid {opt} length"
            
    ans = row.get('correct_answer', '')
    if ans not in ['A', 'B', 'C', 'D']:
        return False, f"Invalid correct_answer: {ans}"
        
    cat = row.get('category', '')
    if cat not in ['aptitude', 'coding', 'core', 'logical', 'verbal', 'numerical']:
        return False, f"Invalid category: {cat}"
        
    diff = row.get('difficulty', '')
    if diff not in ['easy', 'medium', 'hard']:
        return False, f"Invalid difficulty: {diff}"
        
    return True, ""

import click

def detect_category(question_text: str) -> str:
    """
    Detects question category from question text using 
    keyword matching. Returns one of ALLOWED_CATEGORIES.
    Priority order: coding → core → numerical → logical 
                    → verbal → aptitude (default)
    """
    q_text_lower = question_text.lower()
    
    coding_kws = ['algorithm', 'function', 'loop', 'array', 'pointer', 'class', 'object', 'compile', 'syntax', 'variable', 'recursion', 'stack', 'queue', 'linked list', 'binary', 'python', 'java', 'c++', 'javascript', 'output of', 'program', 'code', 'exception', 'inheritance', 'polymorphism', 'encapsulation', 'abstraction', 'sql', 'query', 'database', 'index', 'join']
    if any(kw in q_text_lower for kw in coding_kws): return 'coding'
    
    core_kws = ['operating system', 'process', 'thread', 'semaphore', 'deadlock', 'memory', 'paging', 'scheduling', 'dbms', 'normalization', 'transaction', 'acid', 'network', 'protocol', 'tcp', 'ip', 'http', 'osi', 'router', 'bandwidth', 'latency', 'oop', 'design pattern', 'solid principle', 'system design', 'cache', 'virtual memory', 'file system', 'interrupt']
    if any(kw in q_text_lower for kw in core_kws): return 'core'
    
    numerical_kws = ['ratio', 'percentage', 'profit', 'loss', 'interest', 'speed', 'time', 'distance', 'work', 'average', 'mean', 'median', 'mode', 'probability', 'permutation', 'combination', 'series', 'arithmetic', 'geometric', 'lcm', 'hcf', 'fraction', 'decimal', 'number']
    if any(kw in q_text_lower for kw in numerical_kws): return 'numerical'

    logical_kws = ['pattern', 'sequence', 'analogy', 'odd one', 'odd one out', 'coding decoding', 'direction', 'ranking', 'syllogism', 'blood relation', 'seating', 'arrangement', 'puzzle', 'matrix', 'series completion', 'figure', 'mirror image']
    if any(kw in q_text_lower for kw in logical_kws): return 'logical'

    verbal_kws = ['synonym', 'antonym', 'grammar', 'vocabulary', 'sentence', 'passage', 'comprehension', 'fill in the blank', 'idiom', 'phrase', 'spelling', 'one word', 'active voice', 'passive voice', 'tense', 'preposition']
    if any(kw in q_text_lower for kw in verbal_kws): return 'verbal'
    
    return 'aptitude'

def load_and_clean_questions_v2(csv_path: str, default_category: str = 'aptitude') -> list[dict]:
    """
    Enhanced loader that supports an optional 'category' column.
    Dataset source: Kaggle – Engineering Aptitude Test Questions
    Author: Keith Zidan Dsouza
    """
    ALLOWED_CATEGORIES = ['aptitude', 'coding', 'core', 'logical', 'numerical', 'verbal']
    DIFFICULTY_LEVELS = ['easy', 'medium', 'hard']
    
    try:
        df = pd.read_csv(csv_path, sep=None, engine='python')
    except FileNotFoundError:
        click.echo(f"Error: File not found - {csv_path}")
        return []
    except pd.errors.EmptyDataError:
        click.echo(f"Error: File is empty - {csv_path}")
        return []
        
    total_rows_read = len(df)
    
    df = df.rename(columns={
        'Question': 'question_text',
        'Option A': 'option_a',
        'Option B': 'option_b',
        'Option C': 'option_c',
        'Option D': 'option_d',
        'Answer': 'correct_answer',
        'Category': 'category',
        'Difficulty': 'difficulty'
    }, errors='ignore')
    
    required_cols = ['question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer']
    df = df.dropna(subset=required_cols)
    for col in df.select_dtypes(['object', 'string']).columns:
        df[col] = df[col].astype(str).str.strip()
    
    for col in required_cols:
        df = df[df[col] != '']
    
    df = df.drop_duplicates(subset=['question_text'], keep='first')
    
    rows_before = len(df)
    df['correct_answer'] = df['correct_answer'].str[0].str.upper()
    df = df[df['correct_answer'].isin(['A', 'B', 'C', 'D'])]
    dropped_at_normalization = rows_before - len(df)
    if dropped_at_normalization > 0:
        click.echo(f"Rows dropped due to invalid answer choices in {csv_path}: {dropped_at_normalization}")
    
    df = df.reset_index(drop=True)
    
    if 'category' in df.columns:
        df['category'] = df['category'].str.strip().str.lower()
        mask = ~df['category'].isin(ALLOWED_CATEGORIES)
        df.loc[mask, 'category'] = df.loc[mask, 'question_text'].apply(detect_category)
    else:
        df['category'] = df['question_text'].apply(detect_category)
        
    if 'difficulty' in df.columns:
        df['difficulty'] = df['difficulty'].str.strip().str.lower()
        df.loc[~df['difficulty'].isin(DIFFICULTY_LEVELS), 'difficulty'] = 'medium'
    else:
        total_cleaned = len(df)
        third = total_cleaned // 3
        def get_difficulty(idx):
            if idx < third: return 'easy'
            elif idx < 2 * third: return 'medium'
            else: return 'hard'
        df['difficulty'] = [get_difficulty(i) for i in range(total_cleaned)]

    result = df.to_dict(orient='records')
    
    click.echo(f"--- Summary for {csv_path} ---")
    click.echo(f"Total rows read: {total_rows_read}")
    click.echo(f"Rows after cleaning: {len(result)}")
    click.echo(f"Rows dropped: {total_rows_read - len(result)}")
    click.echo(f"Category distribution:\n{df['category'].value_counts().to_string()}")
    click.echo(f"Difficulty distribution:\n{df['difficulty'].value_counts().to_string()}")
    click.echo("-------------------------------")
    
    return result

