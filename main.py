#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as kungfupanda                    # pandas
from pandas import DataFrame

from os import listdir                          # for file retrieval and path calculations
from os.path import isfile, join
from os import stat

from typing import Set, Dict, List, Tuple       # misc. QOL imports
from collections import defaultdict
from icecream import ic                         # for debugging / outputs

from os.path import getmtime, getctime          # retreiving file creation/modification times
from datetime import datetime
import time

import pickle                                   # for saving/loading json records and file 
                                                # modification date history

from os import getenv                           # for environment variables
from dotenv import load_dotenv, find_dotenv     # for config purposes (.env file)
load_dotenv(find_dotenv(), override=True)

import re                                       # for regex file name matching
from typing import List                         # misc.

from functools import cache                     # for redundancy


# In[ ]:


README_PATH                 = getenv('README_PATH')
LEETCODE_PATH_FROM_README   = getenv('QUESTIONS_PATH_FROM_README')
LEETCODE_PATH_REFERENCE     = join(README_PATH, LEETCODE_PATH_FROM_README)


# ## Helper Methods
# 
# AddCase $\rightarrow$ takes information for a new question file and formats it accordingly for a row.
# 
# UpdateLanguage $\rightarrow$ if a question already has a solution, this is called instead to insert the new file link to the existing row details.

# In[ ]:


# Categories besides those in lists
PRIMARY_CATEGORIES = set(['Daily', 'Weekly Premium', 'Contest', 'Favourite'])


# In[ ]:


def getCtimeMtimes(path: str) -> tuple :    # output: creation, modification
    creation_date = time.ctime(getctime(path))
    modification_date = time.ctime(getmtime(path))

    creation_date = datetime.strptime(creation_date, "%a %b %d %H:%M:%S %Y")
    modification_date = datetime.strptime(modification_date, "%a %b %d %H:%M:%S %Y")

    # I've sometimes encountered weird meta data issues so just as a precaution
    if creation_date > modification_date :
        return (modification_date, creation_date)
    return (creation_date, modification_date)


# In[ ]:


def addCase(level:              str,
            number:             int, 
            title:              str, 
            categories:         Set[str],
            language:           str,
            notebook_path:      str,
            readme_path:        str,
            fileLatestTimes:    dict) -> dict :

    creation_date, modification_date = getCtimeMtimes(notebook_path)
    fileLatestTimes[readme_path] = modification_date

    try :
        fileSize = stat(notebook_path).st_size
    except FileNotFoundError as fnfe :
        fileSize = 0
        print(fnfe)
    

    if not categories :
        categories = set()

    if 'e' in level.lower() :
        level = 'Easy'
    elif 'm' in level.lower() : 
        level = 'Medium'
    elif 'h' in level.lower() :
        level = 'Hard'
    else :
        level = 'Unknown'

    output = {
                'level':                level,
                'number':               number,
                'title':                title, 
                'categories':           categories,
                'date_done':            creation_date,          # First time completed
                'date_modified':        modification_date,      # Most recent date
                'solution':             '',
                'solutions':            {language: [readme_path]},
                'languages':            set([language]),
                'bytes':                fileSize
             }

    return output


# In[ ]:


def updateQuestion(orig:               dict, 
                   *,
                   language:           str,
                   categories:         Set[str],
                   notebook_path:      str,
                   readme_path:        str,
                   fileLatestTimes:    dict) -> dict :  
    
    # Another question file found
    if language and language not in orig['languages'] :
        orig['languages'].add(language)
          
    if categories :
        orig['categories'] |= categories

    if notebook_path and readme_path :
        creation_date, modification_date = getCtimeMtimes(notebook_path)
        
        if creation_date < orig['date_done'] :
            orig['date_done'] = creation_date
        if modification_date > orig['date_modified'] :
            orig['date_modified'] = modification_date
            fileLatestTimes[readme_path] = modification_date

        if language not in orig['solutions'] :
            orig['solutions'][language] = []
        orig['solutions'][language].append(readme_path)

        try :
            fileSize = stat(notebook_path).st_size
        except FileNotFoundError as fnfe :
            fileSize = 0
            print(fnfe)
        orig['bytes'] += fileSize
  
    return orig


# # Pickle Processes
# 

# In[ ]:


@cache
def retrieveQuestionDetails() -> dict :
    question_data_folder    = getenv('QUESTION_DATA_PATH')
    question_details_file   = getenv('LEETCODE_QUESTION_DETAILS')

    if not isfile(join(question_data_folder, question_details_file)) :
        print('Rerunning json-to-pkl parse and export due to the file(s) not being found.')
        print()
        import parse_official_question_data
        
    if not isfile(join(question_data_folder, question_details_file)) :
        print('\nError in parsing official question data. Exiting...')
        print()
        exit()
    else : 
        print('\nFiles found. Importing now...\n')


    # schema: key=int(questionNumber)   val=(title, titleSlug, paidOnly, difficulty, acRate)
    with open(join(question_data_folder, question_details_file), 'rb') as fp:
        questionDetailsDict = pickle.load(fp)
        # print('Question Details dictionary')
        # print(questionDetailsDict)

    return questionDetailsDict


# In[ ]:


@cache
def retrieveQuestionTopics() -> dict :
    question_data_folder    = getenv('QUESTION_DATA_PATH')
    question_topics_file   = getenv('LEETCODE_QUESTION_TOPICS')

    if not isfile(join(question_data_folder, question_topics_file)) :
        print('Rerunning json-to-pkl parse and export due to the file(s) not being found.')
        print()
        import parse_official_question_data
        
    if not isfile(join(question_data_folder, question_topics_file)) :
        print('\nError in parsing official question data. Exiting...')
        print()
        exit()
    else : 
        print('\nFiles found. Importing now...\n')

    # schema: key-int(questionNumber)   val=List[str](topics)
    questionTopicsDict = None
    with open(join(question_data_folder, question_topics_file), 'rb') as fp:
        questionTopicsDict = pickle.load(fp)
        # print('Question Details dictionary')
        # print(questionTopicsDict)

    return questionTopicsDict


# In[ ]:


def writeRecentFileTimes(fileLatestTimes: dict) -> bool :
    history_path = join(getenv('USER_DATA_PATH'), getenv('FILE_MODIFICATION_NAME'))

    with open(history_path, 'wb') as fp:
        pickle.dump(fileLatestTimes, fp)

    return True


# In[ ]:


def getRecentFileTimes() -> dict :
    history_path = join(getenv('USER_DATA_PATH'), getenv('FILE_MODIFICATION_NAME'))

    if isfile(history_path) :
        with open(history_path, 'rb') as fp:
            return pickle.load(fp)
        
    return {}


# # Parsing Files
# Question file parsing occurs here. It organizes it into 3 different lists, separated by difficulty and sorted by question number afterwards.

# In[ ]:


# Parse one leetcode answer file in the submissions folder
def parseCase(leetcodeFile:         str, # file name
              questionData:         dict, # dictionary of question data
              fileLatestTimes:      dict,
              reprocessMarkdown:    set,
              *,
              questionDetailsDict:  dict = retrieveQuestionDetails(),
              subFolderPath:        str = '',
              altTitle:             str = '',
              contest:              bool = False) -> bool:

    path = join(LEETCODE_PATH_FROM_README, subFolderPath, leetcodeFile).replace("\\", "/")
    
    if leetcodeFile[0].isnumeric() :
        number      = int(leetcodeFile[:leetcodeFile.find('.')])
        level       = questionDetailsDict[number][3][0].lower()
    else :
        level       = leetcodeFile[0].lower()
        number      = int(re.sub("[^0-9]", "", leetcodeFile.split(' ')[0]))  # Strips non-numeric chars and any that
                                                                            # follow the question number
                                                                         # e.g. 'e123 v1.py' becomes 123

    creationtime, modificationtime = getCtimeMtimes(join(README_PATH, path))

    if path not in fileLatestTimes or max(creationtime, modificationtime) > fileLatestTimes[path] :
        reprocessMarkdown.add(number)
        fileLatestTimes[path] = max(creationtime, modificationtime)
        

    if number in questionDetailsDict :
        title   = f'[{questionDetailsDict[number][0]}](<https://leetcode.com/problems/{questionDetailsDict[number][1]}>)'
    else :
        title   = f'Question {number}'
    categories  = set()
    language    = leetcodeFile[leetcodeFile.rfind('.') + 1:]

    if len(altTitle) > 0 :
        title = altTitle

    # Question is from a contest folder
    if contest :
        temp = re.findall('q\d{1}', leetcodeFile)                       # Checking if file name has a question number (e.g. q1 of the contest)
        if not len(temp) == 0 :
            title += ' - ' + temp[0]
        # print(title)

    if contest :
        categories.add('Contest')
    else :
        for cat in PRIMARY_CATEGORIES :
            if cat.lower() in leetcodeFile.lower() :
                categories.add(cat)

    if number in questionData :                                     # If solution already found for this question
        questionData[number] = updateQuestion(questionData[number], 
                                              language=language, 
                                              categories=categories, 
                                              notebook_path=join(README_PATH, path), 
                                              readme_path=path,
                                              fileLatestTimes=fileLatestTimes)
        return True
    
    questionData[number] = addCase(level=level, 
                                   number=number, 
                                   title=title,
                                   categories=categories, 
                                   language=language, 
                                   notebook_path=join(README_PATH, path), 
                                   readme_path=path,
                                   fileLatestTimes=fileLatestTimes)
    return True


# In[ ]:


def getCodeFiles() -> List[str] :
    return [x for x in listdir(LEETCODE_PATH_REFERENCE) if isfile(join(LEETCODE_PATH_REFERENCE, x))
                                                           and not x.endswith('.txt')
                                                           and not x.endswith('.md')
                                                           and '.' in x]

def getContextFiles() -> List[str] :
    return [x for x in listdir(LEETCODE_PATH_REFERENCE) if isfile(join(LEETCODE_PATH_REFERENCE, x)) 
                                                           and (x.endswith('.txt') 
                                                                or x.endswith('.md') 
                                                                or '.' not in x)]

def getContestFolders() -> List[str] :
    return [x for x in listdir(LEETCODE_PATH_REFERENCE) if not isfile(join(LEETCODE_PATH_REFERENCE, x))]

def getContestFiles(contestFolders: List[str]) -> List[Tuple[str, str]] :
    contestLeetcodeFiles    = []

    for contestFolder in contestFolders :
        contestLeetcodeFiles.extend([(contestFolder, fileName) for fileName in listdir(join(LEETCODE_PATH_REFERENCE, contestFolder)) 
                                                                if isfile(join(LEETCODE_PATH_REFERENCE, contestFolder, fileName))])
    
    return contestLeetcodeFiles



# # Sort TXT Context
# If .txt notes are placed, this adds them to their respective entry.

# In[ ]:


def parseContextFiles(txtFiles: str, 
                      questionData: dict,
                      fileLatestTimes: dict, 
                      reprocessMarkdown: Set[int]) -> None:
    for fileName in txtFiles :
        # print(f'Context file found: {fileName}')

        number      = int(re.sub("[^0-9]", "", fileName.split(' ')[0]))
        if number not in questionData :
            print(f'Error. No question solution found for context file ({fileName = })')
            continue
        
        questionData[number]['contextFile'] = join(LEETCODE_PATH_FROM_README, fileName)
        path = join(LEETCODE_PATH_REFERENCE, fileName)
        
        creationtime, modificationtime = getCtimeMtimes(path)
        if path not in fileLatestTimes or max(creationtime, modificationtime) > fileLatestTimes[path] :
            fileLatestTimes[path] = max(creationtime, modificationtime)
            reprocessMarkdown.add(number)


# # List-Based Categories
# Updating `Category` columns based on the lists in the `Lists` directory.

# In[ ]:


LISTSDIR = getenv('LISTS_LOCATION')

@cache
def getLists() -> List[str] :

    listFileNames = [x for x in listdir(LISTSDIR) if isfile(join(LISTSDIR, x)) 
                                                    and not x.startswith('.')
                                                    and not x == 'README.md']
    print(listFileNames)

    return listFileNames


# In[ ]:


''' Format for lists file is as follows:

        [Question #]. [Question Name]

        [Easy, Med., Hard]
        Topic1
        Topic2
        Topic3
        ...
'''

@cache
def getList(fileName, filePath) -> set[int] :
    output = set() # can change to dict later if we want to output category info

    count = 0
    with open(filePath, 'r') as file :
        lines = file.readlines()
        for line in lines :
            if re.match(r'\d{1,4}\.', line) :
                count += 1
                output.add(int(line[:line.find('.')]))
    
    return output
    


# In[ ]:


def processListData(questionData: dict,
                    *,
                    listFileNames: List[str] = getLists()) -> dict :
    
    listData = {}
    for file in listFileNames :
        listData[file] = getList(file, join(LISTSDIR, file))
        for q in listData[file] :
            if q in questionData :
                questionData[q]['categories'].add(file)
                
    # print(listData)

    return listData


# # Question Topic Grouping
# Parses the questions in `questionData` and adds their numbers to appropriate lists so that they can be parsed into their own lists as well as counted.

# In[ ]:


def getCompletedQuestionsTopicLists(questionData: dict,
                                    *,
                                    questionTopicsDict: dict = retrieveQuestionTopics()) -> defaultdict :
    
    completedTopicLists = defaultdict(set)

    for question in questionData.keys() :
        if question not in questionTopicsDict :
            continue
        for topic in questionTopicsDict[question] :
            completedTopicLists[topic].add(question)

    return completedTopicLists


# # Individual Markdown Generation
# 

# In[ ]:


README_PATH                     = getenv('README_PATH')
QUESTIONS_FOLDER_FROM_README    = getenv('QUESTIONS_PATH_FROM_README')
QUESTIONS_FOLDER                = join(README_PATH, QUESTIONS_FOLDER_FROM_README)

MARKDOWN_PATH = getenv('QUESTION_MARKDOWNS_PATH_FROM_README')
MARKDOWN_TO_SUBMISSIONS = '../' * MARKDOWN_PATH.count('/') + QUESTIONS_FOLDER_FROM_README

QUESTION_DATA_FOLDER_PATH    = getenv('QUESTION_DATA_PATH')
QUESTION_TOPICS_FILE         = getenv('LEETCODE_QUESTION_TOPICS')
QUESTION_DETAILS_FILE        = getenv('LEETCODE_QUESTION_DETAILS')

LANGUAGE_EQUIVS = {
    'bash': 'Bash',
    'c': 'C',
    'cpp': 'C++',
    'cs': 'C#',
    'csharp': 'C#',
    'go': 'Go',
    'java': 'Java',
    'javascript': 'JavaScript',
    'js': 'JavaScript',
    'kotlin': 'Kotlin',
    'kt': 'Kotlin',
    'lua': 'Lua',
    'm': 'Objective-C',
    'mysql': 'SQL',
    'objc': 'Objective-C',
    'perl': 'Perl',
    'php': 'PHP',
    'py': 'Python',
    'python': 'Python',
    'r': 'R',
    'racket': 'Racket',
    'rb': 'Ruby',
    'rs': 'Rust',
    'ruby': 'Ruby',
    'rust': 'Rust',
    'scala': 'Scala',
    'sh': 'Bash',
    'sql': 'SQL',
    'swift': 'Swift',
    'ts': 'TypeScript',
    'typescript': 'TypeScript'
}


# In[ ]:


# MARKDOWN_TO_SUBMISSIONS
def generate_markdown(questionNo: int, 
                      questionData: dict,
                      *,
                      questionDetailsDict: dict = retrieveQuestionDetails(),
                      questionTopicsDict: dict = retrieveQuestionTopics(),
                      export: bool = False) -> str :
    if questionNo in questionData :
        questionData = questionData[questionNo]

    title = questionData["title"][questionData["title"].find('[') + 1:questionData["title"].find(']')]
    title = f'{questionNo}. {title}'
    
    generate_file_name = f'_{title}.md'
    generate_path = join(README_PATH, MARKDOWN_PATH, generate_file_name)
    output_path = join(MARKDOWN_PATH, generate_file_name)
    
    questionData['solution'] = generate_file_name

    if not export :
        return generate_path

    with open(generate_path, 'w', encoding='utf-8') as f :
        f.write(f'# {questionNo}. {questionData["title"]}\n\n')

        date_done = questionData['date_done']
        date_modified = questionData['date_modified']
        
        f.write(f'*All prompts are owned by LeetCode. To view the prompt, click the title link above.*\n\n')
        f.write('*[Back to top](<../README.md>)*\n\n')

        f.write('------\n\n')
        f.write(f'> *First completed : {date_done:%B %d, %Y}*\n>\n')
        f.write(f'> *Last updated : {date_modified:%B %d, %Y}*\n\n\n')
        f.write('------\n\n')

        BY_TOPIC_FOLDER_PATH = getenv('TOPIC_MARKDOWN_PATH_IN_MARKDOWNS_FOLDER')
        tpcs = 'N/A' if questionNo not in questionTopicsDict else questionTopicsDict[questionNo]
        f.write(f'> **Related Topics** : **' + ', '.join([f'[{x}](<{join(BY_TOPIC_FOLDER_PATH, x)}.md>)' for x in tpcs]) + '**\n>\n')

        acrate = 'Unknown' if questionNo not in questionDetailsDict else f'{questionDetailsDict[questionNo][4]} %'
        f.write(f'> **Acceptance Rate** : **' + f'{acrate}' + '**\n\n\n')
        f.write('------\n\n')

        if 'contextFile' in questionData:
            with open(join(README_PATH, questionData['contextFile']), 'r') as contextFile:
                f.write('> ' + contextFile.read().replace('\n', '\n> '))
            f.write(f'\n\n------\n\n')

        # print(questionData['solutions'])
        

        f.write(f'## Solutions\n\n')
        for lang, solutions in questionData['solutions'].items() :
            solutions.sort()
            for solution in solutions :
                name = solution[solution.find('/') + 1:]
                f.write(f'- [{name}](<{join(README_PATH, solution)}>)\n')

        for lang, solutions in questionData['solutions'].items() :
            if lang.lower() in LANGUAGE_EQUIVS :
                lang = LANGUAGE_EQUIVS[lang.lower()]
            else :
                print()
                print(f'Lang equiv not found: {lang = }')
            f.write(f'### {lang}\n')
            for solution in solutions :
                name = solution.rfind('/') + 1
                f.write(f'#### [{solution[name:]}](<{join(README_PATH, solution)}>)\n')
                f.write(f'```{lang}\n')
                with open(join(README_PATH, solution), 'r', encoding='utf-8') as solutionFile:
                    fileData = solutionFile.read()
                    if '# @lc code=start' in fileData :
                        lcStart = '# @lc code=start'
                        lcEnd   = '# @lc code=end'
                        fileData = fileData[fileData.find(lcStart) + len(lcStart):fileData.rfind(lcEnd)]
                    f.write(fileData)
                f.write('\n```\n\n')

    return output_path


# In[ ]:


def processMarkdownGeneration(questionData: dict,
                              reprocessMarkdown: Set[int],
                              *,
                              questionDetailsDict: dict = retrieveQuestionDetails(),
                              questionTopicsDict: dict = retrieveQuestionTopics()) -> None :
    for questionNo, dta in questionData.items() :
        if questionNo in reprocessMarkdown :
            generate_markdown(questionNo, 
                              questionData, 
                              questionDetailsDict=questionDetailsDict, 
                              questionTopicsDict=questionTopicsDict,
                              export=True)
        else : # In order to assign the markdown paths
            generate_markdown(questionNo, 
                              questionData, 
                              questionDetailsDict=questionDetailsDict, 
                              questionTopicsDict=questionTopicsDict,
                              export=False)


# # DataFrames
# Conversion into DataFrames and declaration of respective column headers occurs here.

# In[ ]:


COLUMNS = [ 
            '#',
            'Title', 
            'Level',
            'Cats',
            'Solution',
            'Languages',
            'Date Complete'
          ]

TYPE_CLARIFICATION = {
                      '#':                  int,
                      'Title':              str, 
                      'Level':              str,
                      'Cats':               str,
                      'Solution':           str,
                      'Languages':          str,
                      'Date Complete':      str
                    }


# In[ ]:


def convertDataToMatrix(questionData: dict,
                        *,
                        sortBy:       str = 'number',
                        includeDate:  bool = False,
                        includeQuestions: set[int] = set(),
                        relativeFolderAdjustment: int = 0,
                        includeMarkdownFolder: bool = False) -> List[list] :
    dataframe_array = []

    for question in questionData.values() :
        # If it's not an empty set and the value isn't in there, skip
        if includeQuestions and question['number'] not in includeQuestions :
            continue

        if sortBy == 'number' and includeMarkdownFolder :
            solution_path = join(MARKDOWN_PATH, question['solution'])    
        else :
            solution_path = question['solution']
        
        solution_path = '../' * abs(relativeFolderAdjustment) + solution_path

        currentRow = [question['number'],
                      question['title'], 
                      question['level'], 
                      ', '.join(list(question['categories'])), 
                      f'[solution](<{solution_path}>)', 
                      ', '.join(list(question['languages']))]
        
        if includeDate :
            currentRow.append(question['date_done'].strftime('%b %d, %Y'))
        
        dataframe_array.append(currentRow)

    dataframe_array.sort(key=lambda x: questionData.get(x[0])[sortBy])
    return dataframe_array


# In[ ]:


def convertQuestionDataToDataframe(questionData: dict,
                                   *,
                                   sortBy: str = 'number',
                                   includeDate:  bool = False,
                                   includeQuestions: set[int] = set(),
                                   relativeFolderAdjustment: int = 0,
                                   includeMarkdownFolder: bool = False) -> DataFrame :
    questionData = convertDataToMatrix(questionData, 
                                       sortBy=sortBy, 
                                       includeDate=includeDate, 
                                       includeQuestions=includeQuestions,
                                       relativeFolderAdjustment=relativeFolderAdjustment,
                                       includeMarkdownFolder=includeMarkdownFolder)
    
    dfQuestions   = kungfupanda.DataFrame(data=questionData, columns=COLUMNS[:len(questionData[0])])
    # dfQuestions   = dfQuestions.astype(TYPE_CLARIFICATION[:len(questionData[0])])

    return dfQuestions


# # List & Other Markdowns

# ## Sorted by Most Recent
# Using creation dates of code files only; not modification dates.

# In[ ]:


# NOTE: Reversed due to default sorting being in ascending order
def byRecentQuestionDataDataframe(questionData: dict) -> DataFrame :
    return convertQuestionDataToDataframe(questionData, sortBy='date_done', includeDate=True).iloc[::-1]


# ## Sorted by Amount of Code
# Questions with more files on the question and longer submissions will be prioritized.

# In[ ]:


def byCodeLengthDataDataframe(questionData: dict) -> DataFrame :
    return convertQuestionDataToDataframe(questionData, sortBy='bytes', includeDate=True).iloc[::-1]


# # Generation of Markdowns for Each Related Topic
# 

# In[ ]:


def questionTopicDataframes(questionData: dict,
                            *,
                            topicGroupings: defaultdict) -> List[Tuple[str, int, DataFrame]] : # [topic, number of questions, dataframe]
    if not topicGroupings :
        topicGroupings = getCompletedQuestionsTopicLists(questionData)
    
    output = []
    for topic, qs in topicGroupings.items() :
        output.append((topic, 
                       len(qs), 
                       convertQuestionDataToDataframe(questionData,
                                                      includeDate=True,
                                                      includeQuestions=qs,
                                                      relativeFolderAdjustment=-getenv('TOPIC_MARKDOWN_PATH_IN_MARKDOWNS_FOLDER').count('/'))))
        
    output.sort(key=lambda x: x[1], reverse=True)
    return output


# In[ ]:


TOPIC_FOLDER = getenv('TOPIC_MARKDOWN_PATH_IN_MARKDOWNS_FOLDER')

def topicBasedMarkdowns(questionData: dict,
                         *,
                         topicGroupings: defaultdict) -> List[Tuple[str, str]] :    # path of all outputs
                                                                                    # list[0]  = overall mardown
                                                                                    # list[1:] = order of count
                                                                                    # doesn't include markdown 'markdown/'
    if not topicGroupings :
        topicGroupings = getCompletedQuestionsTopicLists(questionData)

    topicDataframes = questionTopicDataframes(questionData=questionData, topicGroupings=topicGroupings)

    # For each topic case
    NOTEBOOK_PATH = join(README_PATH, MARKDOWN_PATH, TOPIC_FOLDER)

    # For the overal hosting markdown
    OVERALL_FILE_NOTEBOOK_PATH = join(README_PATH, MARKDOWN_PATH, 'Topics.md')
    OVERALL_FILE_README_PATH = join(MARKDOWN_PATH, 'Topics.md')

    output = [OVERALL_FILE_README_PATH]
    with open(OVERALL_FILE_NOTEBOOK_PATH, 'w', encoding='utf-8') as topic_file :
        topic_file.write('# Topics\n\n')
        topic_file.write('*[Back to top](<../README.md>)*\n\n')
        topic_file.write('------\n\n')

        for topic, cnt, df in topicDataframes :
            file_name = f'{topic}.md'
            notebook_path = join(NOTEBOOK_PATH, file_name)
            readme_path = join(TOPIC_FOLDER, file_name)
            with open(notebook_path, 'w', encoding='utf-8') as f :
                url = f'https://leetcode.com/tag/{topic.replace(" ", "-")}/'
                f.write(f'# [{topic}](<{url}>) ({cnt} completed)\n\n')
                f.write(f'*[Back to top](<../../README.md>)*\n\n')
                f.write('------\n\n')
                f.write(df.to_markdown(index=False))
        
            topic_file.write(f'- [{topic}](<{readme_path}>) ({cnt} completed)\n')
            output.append((topic, readme_path))

    # print(f'topic readme output: {output}')
    return output


# ## Exports

# ## Dailies, Recents, etc.

# In[ ]:


DAILY_URL = ''

def miscMarkdownGenerations(questionData:   dict,
                            *,
                            code_length:    bool = False,
                            recent:         bool = False,
                            daily:          bool = False) -> str : # output path
    df = None
    fileName = None
    header_data = None
    details = None

    # print(f'{code_length, recent = }')
    if code_length :
        df = byCodeLengthDataDataframe(questionData)
        fileName    = 'Questions_By_Code_Length.md'
        header_data = '# Questions By Code Length\n\n'
        details     = 'Calculations are based on the code files\'s byte sizes.\n\n'
    elif recent :
        df = byRecentQuestionDataDataframe(questionData)
        fileName    = 'Questions_By_Recent.md'
        header_data = '# Most Recently Solved Questions\n\n'
        details     = 'Calculations are based on the date of the first solve.\n\n'
    elif daily :
        dailyQuestionData = {}
        for qNo, qData in questionData.items() :
            if 'Daily' in qData['categories'] :
                dailyQuestionData[qNo] = qData
        df = byRecentQuestionDataDataframe(dailyQuestionData)
        fileName    = 'Daily_Questions.md'
        # header_data = f'# [Daily Questions](<{DAILY_URL}>)\n\n'
        header_data = f'# Daily Questions\n\n'
        details     = 'Dates are for the date I completed the ' + \
                      'question so due to the my time zone and how it lines up with ' + \
                      'UTC, it may be off by a day.\n\n'
    else :
        print('Error. No markdown generation specified.')
        print()
        return ''

    # print(f'{fileName = }')

    output_path = join(MARKDOWN_PATH, fileName)
    readme_path = join(README_PATH, MARKDOWN_PATH, fileName)

    with open(readme_path, 'w', encoding='utf-8') as f :
        f.write(header_data)
        f.write(f'*[Back to top](<../README.md>)*\n\n')
        f.write(details)
        f.write(df.to_markdown(index=False))

    return output_path


# # Outputing to README File
# Takes all the above and overwrites the current [README.md](README.md) file with the data calculated above.
# 
# Inputs values in order of:
# - Profile link
# - Stats
# - Stat clarification
# - Question link tables Easy-Medium-Hard
# 
# Uses the built-in DataFrame `.to_markdown()` for outputting.

# In[ ]:


def exportPrimaryReadme(dfQuestions:        DataFrame,
                        *,
                        additionalSorts:    List[str] = [],
                        topicLinks:         List[Tuple[str, str]] = []) -> None :
    readmePath = join(README_PATH, 'README.md')
    print(readmePath)
    with open(readmePath, 'w') as file :
        username = getenv('LEETCODE_USERNAME')
        file.write(f'# **[LeetCode Records](https://leetcode.com/u/{username}/)** ({len(dfQuestions.index)} solved)\n\n')

        file.write(f'> My LeetCode Profile: [{username}](https://leetcode.com/u/{username}/)\n\n')

        file.write('## About this Repo\n\n')
        file.write('This repo is a collection of my LeetCode solutions, primarily written in Python, Java, and C. ' + 
                   'On any page, `click the main title` to be redirected to the official `LeetCode` page for the ' + 
                   'question, topic, list, etc. See the `Additional Categories` section for pages that group' + 
                   ' questions by different criteria -- e.g. by their *related topics*.')
        file.write('\n\n\n')

        file.write('------\n\n')

        file.write('## Category Notes\n')
        file.write('1. **Daily** - Daily challenge questions that were done on the day of\n')
        file.write('2. **Weekly Premium** - Weekly premium questions that were done on week of\n')
        file.write('3. **Contest** - Questions that I completed during a live contest\n')
        # file.write('4. **Favourite** - Questions that I liked and wanted to keep a record of\n')
        file.write('\n\n')

        file.write('------\n\n')

        file.write('## Additional Categories Stats\n')

        for altSorts in additionalSorts :
            file.write(altSorts)
            file.write('\n\n')
        
        if topicLinks :
            file.write('------\n\n')
            file.write(', '.join([f'[{topic}](<{join(MARKDOWN_PATH, link)}>)' for topic, link in topicLinks[1:]]))       
            file.write('\n\n')
            file.write('------\n\n')
        
        file.write('\n\n')

        file.write('## Questions\n')
        file.write(dfQuestions.to_markdown(index=False))


# In[ ]:


# recalculateAll: forces recalcualtion markdowns for each question irregardless if its
#                 source files have been modified or not
def main(*, recalculateAll: bool = False) -> None :
    leetcodeFiles           = getCodeFiles()
    additionalInfoFiles     = getContextFiles()             # For later use when generating the individual readme files

    contestFolders          = getContestFolders()
    contestLeetcodeFiles    = getContestFiles(contestFolders)

    questionDetailsDict     = retrieveQuestionDetails()
    questionTopicsDict      = retrieveQuestionTopics()

    leetcodeFiles.sort()
    contestLeetcodeFiles.sort()


    # Files for leetcode questions found
    # print(leetcodeFiles)
    print(f'Total of {len(leetcodeFiles)} files found.')

    # Files in contest folders found
    # print(contestLeetcodeFiles)
    print(f'Total of {len(contestLeetcodeFiles)} contest files found.')

    # print(questionDetailsDict)


    # Parsing primary files
    fileLatestTimes = getRecentFileTimes() if not recalculateAll else {}

    reprocessMarkdown = set()
    questionData = {}

    # print(f'{fileLatestTimes = }')

    for leetcodeFile in leetcodeFiles :
        parseCase(leetcodeFile=leetcodeFile,
                  questionData=questionData,
                  fileLatestTimes=fileLatestTimes, 
                  reprocessMarkdown=reprocessMarkdown,
                  questionDetailsDict=questionDetailsDict)
        
    # Parsing contest files & folforders
    for leetcodeContestFile in contestLeetcodeFiles :
        contestFolder, leetcodeFile = leetcodeContestFile
        parseCase(leetcodeFile=leetcodeFile,
                  questionData=questionData,
                  fileLatestTimes=fileLatestTimes,
                  reprocessMarkdown=reprocessMarkdown, 
                  altTitle=contestFolder, 
                  subFolderPath=contestFolder, 
                  questionDetailsDict=questionDetailsDict,
                  contest=True)
        

    parseContextFiles(txtFiles=additionalInfoFiles, 
                      questionData=questionData,
                      fileLatestTimes=fileLatestTimes,
                      reprocessMarkdown=reprocessMarkdown)
    
    processListData(questionData=questionData)

    processMarkdownGeneration(questionData=questionData, 
                              reprocessMarkdown=reprocessMarkdown, 
                              questionDetailsDict=questionDetailsDict, 
                              questionTopicsDict=questionTopicsDict)
    
    # Produces a markdown where questions are sorted by the amount of code
    # written for the question
    # code_length_md_path = exportCodeLengthMarkdown(questionData)
    byCodeLength        = miscMarkdownGenerations(questionData, code_length=True)
    byRecentlySolved    = miscMarkdownGenerations(questionData, recent=True)
    dailyQuestions      = miscMarkdownGenerations(questionData, daily=True)
    altSorts            = [f'- [Daily Questions](<{dailyQuestions}>)',
                           f'- [Questions By Code Length](<{byCodeLength}>)',
                           f'- [Questions By Recent](<{byRecentlySolved}>)']
    

    completedQsTopicGroupings = getCompletedQuestionsTopicLists(questionData)
    topicMarkdownLinks = topicBasedMarkdowns(questionData, topicGroupings=completedQsTopicGroupings)
    altSorts.append(f'- [Grouped by Topic](<{topicMarkdownLinks[0]}>)')
    # print(topicMarkdownLinks)


    dfQuestions = convertQuestionDataToDataframe(questionData, includeDate=False, includeMarkdownFolder=True)
    exportPrimaryReadme(dfQuestions, additionalSorts=altSorts, topicLinks=topicMarkdownLinks)

    print(f'Number of individual questions updated/added: {len(reprocessMarkdown)}')


    writeRecentFileTimes(fileLatestTimes)           # restore for next use

    # print(len(questionData))

    return questionData, reprocessMarkdown


# In[ ]:


import argparse



if __name__ == '__main__' :
    parser = argparse.ArgumentParser()
    
    parser.add_argument("-r", 
                        help="Recompile all markdown files", 
                        required=False, 
                        action=argparse.BooleanOptionalAction)

    main(recalculateAll=parser.parse_args().r)


# In[ ]:



