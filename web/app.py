import os
from scripts import vision_detect, speech_detect, video_detect, image_generate

from flask import (Flask, redirect, render_template, request,
                   send_from_directory, url_for)

app = Flask(__name__)
speechanalysisqueries =[]

@app.route('/')
def index():
   print('Request for index page received')
   return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/imagevision', methods=['GET'])
def imagevision():
    tabselected = request.args.get('tabselected')
    print('Request for imagevision received with tabselected=%s' % tabselected)
    return render_template('imagevision.html', tabselected=tabselected)

@app.route('/speechanalysis')
def speechanalysis():
   speechanalysisqueries = []
   tabselected = request.args.get('tabselected')
   print('Request for speech analysis received')
   return render_template('speechanalysis.html', tabselected=tabselected)

@app.route('/videoanalyse')
def videoanalyse():
   speechanalysisqueries = []
   tabselected = request.args.get('tabselected')
   print('Request for video analysis received')
   return render_template('videoanalysis.html', tabselected=tabselected)

@app.route('/defect', methods=['GET'])
def defect():
    image = request.args.get('image')
    ref_image = request.args.get('refImage')
    jsonOutput = request.args.get('jsonOutput')
    tabselected = request.args.get('tabselected')
    if image and ref_image:
        print('Request for defect detection received with image=%s and refImage=%s' % (image, ref_image))
        result = vision_detect.getdefectdetails(image, ref_image, jsonOutput)
        return render_template('imagevision.html', result=result, tabselected=tabselected)
    else:
        print('Request for defect detection received with missing image or refImage -- redirecting')
        return redirect(url_for('imeagevision'))
    
@app.route('/chatwithdata', methods=['GET'])
def chatwithdata():
    message = request.args.get('query')
    tabselected = request.args.get('tabselected')
    if message != "":
        print('Requesting an answer for quetion {message}')
        result = vision_detect.getChatResult(message)
        return render_template('imagevision.html', chatdataresult=result, tabselected=tabselected)
    else:
        print('Request for chat meesage received with emptry string -- redirecting')
        return redirect(url_for('imagevision'))
    

@app.route('/imagegenerate', methods=['GET'])
def imagegenerate():
    message = request.args.get('query')
    tabselected = request.args.get('tabselected')
    if message != "":
        print('Requesting an image based on {message}')
        result = image_generate.generate_image(message)
        return render_template('imagevision.html', generated_image=result, tabselected=tabselected)
    else:
        print('Request for chat meesage received with emptry string -- redirecting')
        return redirect(url_for('imagevision'))
    
@app.route('/speechtotext', methods=['GET'])
def speechtotext():
    speechanalysisqueries = []
    tabselected = request.args.get('tabselected')
    result = speech_detect.audiotranscription()
    if result:
        return render_template('speechanalysis.html', speechtranscriptionresult=result, tabselected=tabselected)
    else:
        print('Request for speech transcription received with empty result -- redirecting')
        return render_template('speechanalysis.html', speechtranscriptionresult="No transcription result received.", tabselected=tabselected)
    
@app.route('/speechqueries', methods=['GET', 'POST'])
def speechqueries():
    request_data = request.get_json()
    queries = request_data.get('queries')
    speechanalysisqueries.extend(queries)
    result = speech_detect.audio_multiturn_conversation(speechanalysisqueries)
    if result:
        print('Request for speech analysis received with queries=%s' % speechanalysisqueries)
        return {"speechanalysisresult": result, "success": True}
    else:
        print('Request for speech transcription received with empty result -- redirecting')
        return {"speechanalysisresult": "No transcription result received.", "success": False}
 
@app.route('/videotranscript', methods=['GET'])
def videotranscript():
    speechanalysisqueries = []
    tabselected = request.args.get('tabselected')
    result = video_detect.video_transcript(True)
    if result:
        return render_template('videoanalysis.html', videotranscriptresult=result, tabselected=tabselected)
    else:
        print('Request for video analysis received with empty result -- redirecting')
        return render_template('videoanalysis.html', videotranscriptresult="No Video Analysis result received.", tabselected=tabselected)

@app.route('/videoanalysis', methods=['GET'])
def videoanalysis():
    speechanalysisqueries = []
    query = request.args.get('query')
    tabselected = request.args.get('tabselected')
    result = video_detect.analyse_video(query)
    if result:
        return render_template('videoanalysis.html', videoanalysisresult=result, tabselected=tabselected)
    else:
        print('Request for video analysis received with empty result -- redirecting')
        return render_template('videoanalysis.html', videoanalysisresult="No Video Analysis result received.", tabselected=tabselected)

@app.route('/hello', methods=['POST'])
def hello():
   name = request.form.get('name')

   if name:
       print('Request for hello page received with name=%s' % name)
       return render_template('hello.html', name = name)
   else:
       print('Request for hello page received with no name or blank name -- redirecting')
       return redirect(url_for('index'))


if __name__ == '__main__':
   app.run()
