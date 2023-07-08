# %%
import pandas as pd
import re
import glob
import os
from datetime import datetime, timedelta
import csv
import xml.etree.ElementTree as ET
import copy
import random
import uuid


final_clip_list = []
id_mapping = {}
# global sequence_start
# global sequence_end

sequence_start=0
sequence_end=0
xml_file_assigned=[]
xml_folder = "../Interview XML/"
exported_xml_project_name= 'testy'
final_subtitle_file = "../final_subtitle.srt"
intermediate_csv_file = '../intermediate.csv'
xls_folder_path = "../Interview XLSX/"
xls_file_extension = ".xlsx"
script_path = "../Script/test script.txt"
output_matched_csv_file = "../matched.csv"
# Folder path containing the text files
TXT_folder_path = '../Interview TXT/'



def extract_paragraphs(file_path):
    with open(file_path, 'r') as file:
        content = file.read()

    regex = r"\[(\d{2}:\d{2}:\d{2})\]\s+(.*?)(?=\n\[|\Z)"
    matches = re.findall(regex, content, re.DOTALL)

    paragraphs = []
    for i, match in enumerate(matches):
        start_time = match[0]
        paragraph = match[1].strip().replace('\n', ' ')  # Remove leading/trailing whitespace and replace newlines with spaces
        
        # Remove line breaks between speaker lines
        paragraph = re.sub(r'([A-Za-z]+:)\s*\n\s*', r'\1 ', paragraph)

        if paragraph:
            if i < len(matches) - 1:
                next_start_time = matches[i + 1][0]
                end_time = next_start_time
            else:
                # Last paragraph, use a default end time
                end_time = "00:00:00"

            paragraphs.append((paragraph, start_time, end_time))

    return paragraphs


def process_paragraph(paragraph, start_time, end_time):
    # Split the paragraph into sentences
    sentences = paragraph.split('. ')
    
    # Calculate the number of sentences
    num_sentences = len(sentences)
    
    # Convert start time and end time to datetime objects
    start_datetime = pd.to_datetime(start_time[1:9], format='%H:%M:%S')
    end_datetime = pd.to_datetime(end_time[1:9], format='%H:%M:%S')
    
    # Calculate the total duration of the paragraph in seconds
    total_duration = (end_datetime - start_datetime).total_seconds()
    
    # Calculate the total number of words in the paragraph
    total_words = len(paragraph.split())
    
    # Calculate the time per word
    time_per_word = total_duration / total_words
    
    # Create a list to store the resulting data
    data = []
    
    # Iterate over each sentence and assign time values
    current_datetime = start_datetime
    for sentence in sentences:
        sentence_words = sentence.split()
        sentence_duration = len(sentence_words) * time_per_word
        
        time_str = f"{current_datetime.time().strftime('%H:%M:%S')} - {(current_datetime + pd.Timedelta(seconds=sentence_duration)).time().strftime('%H:%M:%S')}"
        data.append([time_str, sentence.strip(), ""])
        current_datetime += pd.Timedelta(seconds=sentence_duration)
    
    # Create a pandas DataFrame
    df = pd.DataFrame(data, columns=['TIME', 'TRANSLATION (ENGLISH)', 'TRANSCRIPTION (SESOTHO)'])
    
    return df


def convert_txt_to_csv_xlsx():
    

    # Get a list of all the text files in the folder
    txt_files = glob.glob(TXT_folder_path + '*.txt')

    for txt_file in txt_files:
        # Extract paragraphs from the current text file
        paragraphs = extract_paragraphs(txt_file)

        df_all = pd.DataFrame(columns=['TIME', 'TRANSLATION (ENGLISH)', 'TRANSCRIPTION (SESOTHO)', 'filepath'])

        for paragraph in paragraphs:
            df = process_paragraph(paragraph[0], '['+paragraph[1]+']', '['+paragraph[2]+']')

            # Add the 'filepath' column with the current text file path
            df['filepath'] = txt_file
            
            df_all = pd.concat([df_all, df], ignore_index=True)

        # Generate the Excel file name based on the text file name
        excel_file = os.path.join(xls_folder_path, os.path.basename(txt_file).replace('.txt', '.xlsx'))
        csv_file = os.path.join(xls_folder_path, os.path.basename(txt_file).replace('.txt', '.csv'))

        # Save the DataFrame to the Excel file
        df_all.to_excel(excel_file, index=False)
        df_all.to_csv(csv_file, index=False)

# convert_txt_to_csv_xlsx()

# %%


def clean_text(text):
    # Remove special characters from the text
    cleaned_text = re.sub(r"[^\w\s]", "", text)
    return cleaned_text

def match_line(line, df):
    cleaned_line = clean_text(line.lower())  
    matched_rows = []
    for _, row in df.iterrows():
        transcription = clean_text(str(row['TRANSCRIPTION (SESOTHO)']).lower())
        translation = clean_text(str(row['TRANSLATION (ENGLISH)']).lower())
        if cleaned_line in transcription or cleaned_line in translation:
            matched_rows.append(row) 
    matched_rows_df = pd.concat(matched_rows, axis=1).transpose() if matched_rows else pd.DataFrame()
    return matched_rows_df

def get_word_indices(full_string, substring):
    full_list = full_string.split()
    sub_list = substring.split()
    length = len(sub_list)
    
    for i in range(len(full_list)):
        if full_list[i:i+length] == sub_list:
            return i, i+length
    return None, None



def match_script_to_csv():


    combined_df = pd.DataFrame()

    for filename in os.listdir(xls_folder_path):
        if filename.endswith(xls_file_extension):
            file_path = os.path.join(xls_folder_path, filename)
            df = pd.read_excel(file_path)
            df['filepath'] = file_path
            combined_df = pd.concat([combined_df, df], ignore_index=True)

    matched_rows = []

    with open(script_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    narrator = None
    language = None
    for line in lines:
        line = line.strip().lower()
        if line.startswith('***'):
            narrator = line[3:].strip().lower()
            language = 'SESOTHO'
        elif line.startswith('###'):
            narrator = line[3:].strip().lower()
            language = 'ENGLISH'
        elif line and narrator and language:
            matched_rows_df = match_line(line, combined_df)
            cleaned_line = clean_text(line)
            if not matched_rows_df.empty:
                for _, row in matched_rows_df.iterrows():
                    time_range = row['TIME'].split(" - ")
                    start_time = datetime.strptime(time_range[0], '%H:%M:%S')
                    end_time = datetime.strptime(time_range[1], '%H:%M:%S')
                    total_duration = (end_time - start_time).total_seconds()

                    transcription = clean_text(str(row['TRANSCRIPTION (SESOTHO)']).lower())
                    translation = clean_text(str(row['TRANSLATION (ENGLISH)']).lower())
                    original_text = transcription if cleaned_line in transcription else translation
                    if cleaned_line == original_text:
                        new_row = {
                            'Text': line,
                            'Narrator': narrator,
                            'Language': language,
                            'Timecode Range': row['TIME'],
                            'FilePath': row['filepath']
                        }
                    else:
                        start_index, end_index = get_word_indices(original_text, cleaned_line)
                        total_words = len(original_text.split())
                        start_time = start_time + timedelta(seconds=total_duration*start_index/total_words)
                        end_time = start_time + timedelta(seconds=total_duration*(end_index-start_index)/total_words)
                        new_row = {
                            'Text': line,
                            'Narrator': narrator,
                            'Language': language,
                            'Timecode Range': f'{start_time.time()} - {end_time.time()}',
                            'FilePath': row['filepath']
                        }
                    matched_rows.append(new_row)
            else:  
                new_row = {
                    'Text': line,
                    'Narrator': narrator,
                    'Language': language,
                    'Timecode Range': None,
                    'FilePath': None
                }
                matched_rows.append(new_row)

    matched_df = pd.DataFrame(matched_rows)
    matched_df.to_csv(output_matched_csv_file, index=False)


# match_script_to_csv()

# %%


def time_to_srt_format(time):
    return str(timedelta(seconds=time)).split('.')[0]

def time_difference(time_str):
    start, end = time_str.split(' - ')
    try:
        FMT = "%H:%M:%S.%f"
        tdelta = datetime.strptime(end, FMT) - datetime.strptime(start, FMT)
    except ValueError:
        try:
            FMT = "%H:%M:%S"
            tdelta = datetime.strptime(end, FMT) - datetime.strptime(start, FMT)
        except ValueError:
            return 0
    return tdelta.total_seconds()

def clean_text(text):
    # Remove special characters from the text
    cleaned_text = re.sub(r"[^\w\s]", "", text)
    return cleaned_text

def generate_subtitles():

    with open(intermediate_csv_file, 'r') as csv_file, open(final_subtitle_file, 'w') as srt_file:
        csv_reader = csv.reader(csv_file)
        next(csv_reader)  # Skip header
        counter = 1
        last_time = 0
        for row in csv_reader:
            srt_file.write(str(counter) + '\n')
            if row[3]:  # If Timecode Range is not empty
                start_time, end_time = row[3].split(' - ')
                time_diff = time_difference(row[3])
                start_seconds = last_time
                end_seconds = last_time + time_diff
                last_time = end_seconds
                start_time = time_to_srt_format(start_seconds)
                end_time = time_to_srt_format(end_seconds)
                srt_file.write(start_time + ',000 --> ' + end_time + ',000\n')
            else:
                start_time = time_to_srt_format(last_time)  # Start time based on last saved end time
                last_time += 5  # Add 5 seconds to the last known time
                end_time = time_to_srt_format(last_time)
                srt_file.write(start_time + ',000 --> ' + end_time + ',000\n')
            srt_file.write(clean_text(row[0]) + '\n\n')  # Cleaned text
            counter += 1

# generate_subtitles()

# %%



def create_xml(xml_name,xml_json_data):
    
    # Create the root element
    root = ET.Element("xmeml", version="4")
    
    # Create the sequence element with attributes
    sequence = ET.SubElement(root, "sequence", id="sequence-2", TL_SQAudioVisibleBase="0", TL_SQVideoVisibleBase="0",
                             TL_SQVisibleBaseTime="0", TL_SQAVDividerPosition="0.5", TL_SQHideShyTracks="0",
                             TL_SQHeaderWidth="236", TL_SQDataTrackViewControlState="0",
                             Monitor_ProgramZoomOut="340011984312000", Monitor_ProgramZoomIn="0",
                             TL_SQTimePerPixel="1.6034289012958367", MZ_EditLine="333083126376000",
                             MZ_Sequence_PreviewFrameSizeHeight="1080", MZ_Sequence_PreviewFrameSizeWidth="1920",
                             MZ_Sequence_AudioTimeDisplayFormat="200", MZ_Sequence_PreviewUseMaxRenderQuality="false",
                             MZ_Sequence_PreviewUseMaxBitDepth="false", MZ_Sequence_VideoTimeDisplayFormat="110",
                             MZ_WorkOutPoint="15235011792000", MZ_WorkInPoint="0", MZ_ZeroPoint="0", explodedTracks="true")
    
    # Add the uuid element
    uuid = ET.SubElement(sequence, "uuid")
    uuid.text = "50e61931-251f-4069-8193-a3fbad7f93ff"
    
    # Add the duration element
    duration = ET.SubElement(sequence, "duration")
    duration.text = "31533"
    
    # Add the rate element with nested timebase and ntsc elements
    rate = ET.SubElement(sequence, "rate")
    timebase = ET.SubElement(rate, "timebase")
    timebase.text = "24"
    ntsc = ET.SubElement(rate, "ntsc")
    ntsc.text = "TRUE"
    
    # Add the name element
    name_element = ET.SubElement(sequence, "name")
    name_element.text = xml_name
    
    # Add the media element with nested video and audio elements
    media = ET.SubElement(sequence, "media")
    video = ET.SubElement(media, "video")

    # Add the format element with nested samplecharacteristics element
    format_ = ET.SubElement(video, "format")
    samplecharacteristics = ET.SubElement(format_, "samplecharacteristics")
    
    # Add the rate element with nested timebase and ntsc elements inside samplecharacteristics
    rate = ET.SubElement(samplecharacteristics, "rate")
    timebase = ET.SubElement(rate, "timebase")
    timebase.text = "24"
    ntsc = ET.SubElement(rate, "ntsc")
    ntsc.text = "TRUE"
    
    # Add the codec element with nested name and appspecificdata elements
    codec = ET.SubElement(samplecharacteristics, "codec")
    name = ET.SubElement(codec, "name")
    name.text = "Apple ProRes 422"
    appspecificdata = ET.SubElement(codec, "appspecificdata")
    
    # Add the appname, appmanufacturer, and appversion elements inside appspecificdata
    appname = ET.SubElement(appspecificdata, "appname")
    appname.text = "Final Cut Pro"
    appmanufacturer = ET.SubElement(appspecificdata, "appmanufacturer")
    appmanufacturer.text = "Apple Inc."
    appversion = ET.SubElement(appspecificdata, "appversion")
    appversion.text = "7.0"
    
    # Add the data element with nested qtcodec element inside appspecificdata
    data = ET.SubElement(appspecificdata, "data")
    qtcodec = ET.SubElement(data, "qtcodec")
    codecname = ET.SubElement(qtcodec, "codecname")
    codecname.text = "Apple ProRes 422"
    codectypename = ET.SubElement(qtcodec, "codectypename")
    codectypename.text = "Apple ProRes 422"
    codectypecode = ET.SubElement(qtcodec, "codectypecode")
    codectypecode.text = "apcn"
    codecvendorcode = ET.SubElement(qtcodec, "codecvendorcode")
    codecvendorcode.text = "appl"
    spatialquality = ET.SubElement(qtcodec, "spatialquality")
    spatialquality.text = "1024"
    temporalquality = ET.SubElement(qtcodec, "temporalquality")
    temporalquality.text = "0"
    keyframerate = ET.SubElement(qtcodec, "keyframerate")
    keyframerate.text = "0"
    datarate = ET.SubElement(qtcodec, "datarate")
    datarate.text = "0"
    
    # Add the width, height, anamorphic, pixelaspectratio, fielddominance, and colordepth elements inside samplecharacteristics
    width = ET.SubElement(samplecharacteristics, "width")
    width.text = "1920"
    height = ET.SubElement(samplecharacteristics, "height")
    height.text = "1080"
    anamorphic = ET.SubElement(samplecharacteristics, "anamorphic")
    anamorphic.text = "FALSE"
    pixelaspectratio = ET.SubElement(samplecharacteristics, "pixelaspectratio")
    pixelaspectratio.text = "square"
    fielddominance = ET.SubElement(samplecharacteristics, "fielddominance")
    fielddominance.text = "none"
    colordepth = ET.SubElement(samplecharacteristics, "colordepth")
    colordepth.text = "24"

    # Get the track elements
    video_tracks = [1]
    audio_tracks = []
    for clip in xml_json_data:

        audio_track_indexes = [link["trackindex"] for link in clip["video_clips"][0]["links"] if link["mediatype"] == "audio"]
        # print(audio_track_indexes)
        for audio_track_index in audio_track_indexes:
            if audio_track_index not in audio_tracks:
                audio_tracks.append(audio_track_index)

    # Create video track elements and append video clips
    for video_track_index in video_tracks:
        video_track = ET.SubElement(video, "track", TL_SQTrackShy="0", TL_SQTrackExpandedHeight="25",
                                    TL_SQTrackExpanded="0", MZ_TrackTargeted="0")
        # video_track.set("trackindex", str(video_track_index))

        for clip in xml_json_data:
            video_clip = clip["video_clips"][0]["video_clip_element"]
            video_track.append(copy.deepcopy(video_clip))

   
    

    
    # Add the audio element inside media
    audio = ET.SubElement(media, "audio")

    # constant stuff

    # Create subelements and append them to the audio element
    num_output_channels = ET.SubElement(audio, 'numOutputChannels')
    num_output_channels.text = '2'

    format_element = ET.SubElement(audio, 'format')
    sample_characteristics = ET.SubElement(format_element, 'samplecharacteristics')
    depth = ET.SubElement(sample_characteristics, 'depth')
    depth.text = '16'
    sample_rate = ET.SubElement(sample_characteristics, 'samplerate')
    sample_rate.text = '48000'

    outputs = ET.SubElement(audio, 'outputs')

    group_1 = ET.SubElement(outputs, 'group')
    index_1 = ET.SubElement(group_1, 'index')
    index_1.text = '1'
    num_channels_1 = ET.SubElement(group_1, 'numchannels')
    num_channels_1.text = '1'
    downmix_1 = ET.SubElement(group_1, 'downmix')
    downmix_1.text = '0'
    channel_1 = ET.SubElement(group_1, 'channel')
    channel_index_1 = ET.SubElement(channel_1, 'index')
    channel_index_1.text = '1'

    group_2 = ET.SubElement(outputs, 'group')
    index_2 = ET.SubElement(group_2, 'index')
    index_2.text = '2'
    num_channels_2 = ET.SubElement(group_2, 'numchannels')
    num_channels_2.text = '1'
    downmix_2 = ET.SubElement(group_2, 'downmix')
    downmix_2.text = '0'
    channel_2 = ET.SubElement(group_2, 'channel')
    channel_index_2 = ET.SubElement(channel_2, 'index')
    channel_index_2.text = '2'

     # Create audio track elements and append audio clips
    for audio_track_index in audio_tracks:
        audio_track = ET.SubElement(audio, "track", TL_SQTrackAudioKeyframeStyle="0", TL_SQTrackShy="0",
                                    TL_SQTrackExpandedHeight="25", TL_SQTrackExpanded="0",
                                    MZ_TrackTargeted="1", PannerCurrentValue="0.5", PannerIsInverted="true",
                                    PannerStartKeyframe="-91445760000000000,0.5,0,0,0,0,0,0", PannerName="Balance",
                                    currentExplodedTrackIndex=f"{audio_track_index-1}", totalExplodedTrackCount="2",
                                    premiereTrackType="Stereo")
        # audio_track.set("trackindex", str(audio_track_index))

        for clip in xml_json_data:
            audio_clip_elements = clip["video_clips"][0]["linked_audio_clip_elements_list"]
            
            for audio_clip in audio_clip_elements:
                if audio_track_index == audio_clip[1]:
                    audio_track.append(copy.deepcopy(audio_clip[0]))
    
    # Add the timecode element with nested rate, string, frame, and displayformat elements
    timecode = ET.SubElement(sequence, "timecode")
    rate = ET.SubElement(timecode, "rate")
    timebase = ET.SubElement(rate, "timebase")
    timebase.text = "24"
    ntsc = ET.SubElement(rate, "ntsc")
    ntsc.text = "TRUE"
    string = ET.SubElement(timecode, "string")
    string.text = "00:00:00:00"
    frame = ET.SubElement(timecode, "frame")
    frame.text = "0"
    displayformat = ET.SubElement(timecode, "displayformat")
    displayformat.text = "NDF"
    
    # Add the labels element with nested label2 element
    labels = ET.SubElement(sequence, "labels")
    label2 = ET.SubElement(labels, "label2")
    label2.text = "Forest"
    


    
    # Create the ElementTree object with the root element
    tree = ET.ElementTree(root)
    
    # Generate a random Idd
    idd = str(random.randint(1, 1000))
    
    # Save the XML to a file
    filename = f"../xml exports/{xml_name.replace(' ', '_')}-{idd}.xml"
    tree.write(filename, encoding="utf-8", xml_declaration=True)
    print(f"XML saved to {filename}")


def generate_unique_id():
    unique_id = f"clipitem-{uuid.uuid4().hex}"
    return unique_id

def update_xml_ids(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    print('Assigning unique IDs to clipitem elements...')

    # Generate unique IDs for clipitem elements
      # Store the mapping of old IDs to new unique IDs
    for clip_item in root.findall('.//clipitem'):  # Adjust the XPath expression based on the actual location of clipitem elements
        current_id = clip_item.attrib['id']
        unique_id = generate_unique_id()
        id_mapping[current_id] = unique_id
        clip_item.attrib['id'] = unique_id

    
        # Update the references in the links section
    for link in root.findall('.//link'):
        linkclipref = link.find('linkclipref')
        if linkclipref is not None and linkclipref.text in id_mapping:
            linkclipref.text = id_mapping[linkclipref.text]
    print(id_mapping)

    # Save the modified XML file
    tree.write(xml_file, encoding="utf-8")



def extract_timecode(timecode_range):
    start_time, end_time = timecode_range.split(" - ")
    start_time = start_time.strip().replace(" ", "")
    end_time = end_time.strip().replace(" ", "")
    print('Start Time',start_time,'End Time', end_time)
    return start_time, end_time


def process_csv_file(csv_file, xml_folder):
    with open(csv_file, "r") as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            timecode_range = row["Timecode Range"]
            if timecode_range:
                start_time, end_time = extract_timecode(timecode_range)
                narrator_name = row["Narrator"]
                print('Narrator Name:' ,narrator_name)
                process_xml_files(xml_folder, start_time, end_time, narrator_name)


def process_xml_files(xml_folder, start_time, end_time, narrator_name):
    global xml_file_assigned,final_clip_list
    for filename in os.listdir(xml_folder):
        if filename.endswith(".xml") and narrator_name in filename:
            # print(filename,narrator_name)
            xml_file = os.path.join(xml_folder, filename)
            if xml_file not in xml_file_assigned:
                update_xml_ids(xml_file)
                xml_file_assigned.append(xml_file)
            matched_clips = extract_sequence_info(xml_file, start_time, end_time)
            final_clip_list.append(matched_clips)


def convert_time_to_frames(time, rate):
    time_format = "%H:%M:%S"
    if "." in time:
        time_format += ".%f"
    time_obj = datetime.strptime(time, time_format)
    time_delta = time_obj - datetime.strptime("00:00:00", "%H:%M:%S")
    frame_count = int(time_delta.total_seconds() * rate)
    return frame_count


def frame_to_ticks(frame_number, frame_rate):
    total_ticks_in_a_second = 254016000000
    tick_value = int((frame_number * total_ticks_in_a_second) / frame_rate)
    return tick_value


def extract_sequence_info(xml_file, start_time, end_time):
    global sequence_start, sequence_end
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Extract sequence information
    sequence = root.find('sequence')
    sequence_info = {
        'duration': int(sequence.find('duration').text),
        'rate': {
            'timebase': int(sequence.find('rate/timebase').text),
            'ntsc': sequence.find('rate/ntsc').text == 'TRUE'
        }
    }
    sequence_rate = sequence_info['rate']['timebase']

    # Convert start and end times to frames
    start_frame = convert_time_to_frames(start_time, sequence_rate)
    end_frame = convert_time_to_frames(end_time, sequence_rate)
    proTickIn=frame_to_ticks(start_frame,sequence_rate)
    proTickOut=frame_to_ticks(end_frame,sequence_rate)
    
    print('Start and End Frame',start_frame ,end_frame)
    print(sequence_rate,'sequence_rate')

    # Extract video clip information
    video_clips = []
    for clip_item in root.findall('.//video//clipitem'):  # Only consider clip items within the <video> tag
        
        clip_info = {
            'id': clip_item.attrib['id'],  # Get the clip ID
            'name': clip_item.find('name').text,
            'duration': int(clip_item.find('duration').text),
            'rate': {
                'timebase': int(clip_item.find('rate/timebase').text),
                'ntsc': clip_item.find('rate/ntsc').text == 'TRUE'
            },
            'in': int(clip_item.find('in').text),
            'out': int(clip_item.find('out').text),
            'start': int(clip_item.find('start').text),
            'end': int(clip_item.find('end').text),
            'links': [],  # Initialize an empty list to store links,
            'video_clip_element': None,  # Store the clip item element for later use
            'linked_audio_clip_elements_list': []  # Initialize an empty list to store linked clip items
        }

        if clip_info['in'] <= start_frame <= clip_info['out']:
            sequence_start=sequence_end+10
            sequence_end=sequence_start+(end_frame-start_frame)

        links = clip_item.findall('link')
        for link in links:
            link_info = {
                'linkclipref': link.find('linkclipref').text,
                'mediatype': link.find('mediatype').text,
                'trackindex': int(link.find('trackindex').text),
                'clipindex': int(link.find('clipindex').text)
            }
            if link.find('groupindex') is not None:
                link_info['groupindex'] = int(link.find('groupindex').text)
            clip_info['links'].append(link_info)
            if link.find('mediatype').text == 'audio':
                audio_clip_items = root.findall('.//audio//clipitem')
                for audio_clip_item in audio_clip_items:
                    if audio_clip_item.attrib['id'] == link.find('linkclipref').text:
                        audio_clip_item.find('in').text = str(start_frame)  
                        audio_clip_item.find('out').text = str(end_frame)
                        audio_clip_item.find('start').text = str(sequence_start)  
                        audio_clip_item.find('end').text = str(sequence_end)
                        audio_clip_item.find('pproTicksIn').text = str(proTickIn)  
                        audio_clip_item.find('pproTicksOut').text = str(proTickOut)
                        clip_info['linked_audio_clip_elements_list'].append([audio_clip_item,int(link.find('trackindex').text)])

        # Check if the clip's in or out frame falls within the given start and end frames
        print('Clip Frame Inside file Found: ',clip_info['in'] <= start_frame <= clip_info['out'])
        print('Start - Matching - End')
        print(clip_info['in'],start_frame,clip_info['out'])
        if clip_info['in'] <= start_frame <= clip_info['out']:
            clip_item.find('in').text = str(start_frame)  
            clip_item.find('out').text = str(end_frame)
            clip_item.find('start').text = str(sequence_start)  
            clip_item.find('end').text = str(sequence_end)
            clip_info['video_clip_element']=clip_item
            video_clips.append(clip_info)
            print('Next Sequence Start',sequence_start)
            print('Next Sequence End',sequence_end)
            
        
    # print(clip_info, start_frame, end_frame)

    # Create result dictionary
    result = {
        'sequence_info': sequence_info,
        'video_clips': video_clips
    }
    # print('Result',result)

    if not video_clips:  # Check if video_clips list is empty
        return None
    
    return result



def run_extraction():
        
    # Example usage
    
    final_clip_list = []
    process_csv_file(intermediate_csv_file, xml_folder)
    final_clip_list = [item for item in final_clip_list if item is not None]
    # print(final_clip_list)
    create_xml(exported_xml_project_name,final_clip_list)
# print(final_clip_list)

# run_extraction()

# %%



