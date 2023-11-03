# AutoPremiere


Steps for syncing and subtitling each interview:

1. Gather all footage into a timeline, named after the code for the interview. Place each camera grouping sequentially, on different tracks. Add temp color. This timeline should be in an ‘unsynced’ bin within ’01_Interviews’ in the project.
2. Clip audio and add to timeline 
3. Export timeline as xml to /01_Interviews/Project Code/XML/unsynced/ on the harddrive.
4. Import xml into Syncaila and synchronize, and export to /01_Interviews/Project Code/XML/syncaila/ on the harddrive. (The name will now be ‘interview code - synced.xml’) 
5. Bring this synced xml into a ’synced’ bin within ’01_Interviews’ in the project. Then, manually fix all files that syncalia couldn’t match or did incorrectly.
6. Shift all media that comes before the audio start time to the end of the timeline, so that the beginning of the clipped audio is at the very start of the timeline.
7. Add back in temp color, and do a quick edit to delete trash footage and select which cameras are on top.
8. Export media as 640wide and set bitrate to 2mbps. Upload to drive in  /Interviews/project code/Video/
9. Export xml to /AutoPremiere/03_Interview XML/Project Code/Interview Code - final.xml
10. If interview is in a language Premiere knows, run the auto-transcribe (set language with ‘static transcript’) and auto-caption tool (set line length to 60 and to single). Export captions as text file and upload to googledrive in  /Interviews/project code/Auto-Transcripts/
11. Have transcriptions/translator use the video file and auto-transcript (if it exists) to create a complete transcript file. Once this is complete, run google translate to convert this file to English. Make sure these are in the correct folders in the googledrive, e.g. /Interviews/project code/Spanish/ and /English/
12. Download transcripts and place them in /AutoPremiere/02_Transcripts/Project Code/Transcripts (EN)/ or /Transcripts (ES)/ respectively. The file names need to be ‘interview code (ES).docx’ or (EN) based on language.
13. Open the Jupyter notebook ‘Docx to Csv to Srt’ in AutoPremiere/00_Code/. (Open terminal, use cd to navigate to AutoPremiere, and execute ‘jupyter notebook’) Set the project code at the top and then run the entire notebook. 
14. Some errors might arise when trying to convert the transcripts to csv, especially for any transcripts that didn’t use auto-transcripts with prebuilt timecodes. Fix any errors by altering the transcript file locally, until no errors come up and the output csv file looks complete. Then reupload that transcript to the googledrive to make sure it has the most updated version.
15. Take the final outputs within /AutoPremiere/05_Subtitles/project code/ and add this file structure to the corresponding bin in the project, 04_Subtitles/. Note that this is easiest to do in bulk by replacing the entire set of srt exports.
16. Drag the corresponding subtitle file onto the timeline (into the video tracks not the subtitle track), so the menu pops up to import, and select ‘source timecode’. Check that the subtitles extend the entire length and don’t cut off early, and if they do then there is a timecode problem in the transcripts that needs to be fixed and rerun.
17. Export this new subtitled version (make sure captions are being burnt in) and add to the googledrive in a ‘Subtitled Video Exports’ folder.
18. Update status on tracking spreadsheet and update metadata on length, location, speakers, etc.


Note that it is easier to do these steps in bulk, e.g. export all unsynced together, then run syncalia over all of them at once.