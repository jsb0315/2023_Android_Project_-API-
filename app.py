from flask import Flask, request, jsonify
import pymysql, random, requests, json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import random, time

chrome_options = Options()
chrome_options.add_argument('headless')
driver = webdriver.Chrome(options=chrome_options)

def OpenDB(sql): #sql 데이터 반환 함수
    db = pymysql.connect(host='203.234.62.169', user='Java', password='1234', 
                                              db='dbproject', charset='utf8')
    cursor = db.cursor()
    cursor.execute(sql)
    result = cursor.fetchall()

    db.commit()
    db.close()
    
    return result

def executesql(arr3, arr4): # sql 생성
    arr4 = [round(i*.7, 3) if type(i)!=str else i for i in arr4]
    sql = 'select f.name, i.ingredient, x1, x2, x3, x4'
    sql_select = ', 1/(sqrt('
    sql_where = ''

    for i in range(4):
        sql_select = sql_select + f'pow({arr4[i]}-x{i+1}, 2)+'  # pow(@n1-x1, 2)+
    sql_select = sql_select[:-1] + ')) norm, '+ \
        f'sqrt({sql_select[10:-1]}) test '+ \
        'from foods f, ingredients i, vector v where f.name=v.name and f.ingredient=i.id'
    sql = sql + sql_select

    for i in range(3):
        tmp = ['country', 'maincategory', '중분류']
        if arr3[i] != '전체':
            if i==0:
                arr3[0]=arr3[0][0]
            sql_where = sql_where + f' and {tmp[i]}="{arr3[i]}"'

    sql += sql_where + ' order by norm desc limit 5;'
    print(sql)
    return sql

def findURL(query):
    driver.get(f'https://search.naver.com/search.naver?&where=image&query={query}')

    for i in range(5):
        try:
            first_image_element = driver.find_element(By.XPATH,f'//*[@id="main_pack"]/section[2]/div[1]/div/div/div[1]/div[{random.randint(1,10)}]/div/div/a/img').get_attribute('src')
            return first_image_element
        except:
            time.sleep(0.02)
    return "none"

app = Flask(__name__)

@app.route('/api/food', methods=['GET'])
def receive_data_food():
    p1 = request.args.get('p1') if request.args.get('p1')!='r' else '전체'
    p2 = request.args.get('p2') if request.args.get('p2')!='r' else '전체'
    p3 = request.args.get('p3') if request.args.get('p3')!='r' else '전체'
    p4 = float(request.args.get('p4')) if request.args.get('p4')!='r' else random.randint(0,70)/10
    p5 = float(request.args.get('p5')) if request.args.get('p5')!='r' else random.randint(0,70)/10
    p6 = float(request.args.get('p6')) if request.args.get('p6')!='r' else random.randint(0,70)/10
    p7 = float(request.args.get('p7')) if request.args.get('p7')!='r' else random.randint(0,70)/10

    print([p1,p2,p3,p4,p5,p6,p7])
    result = pd.DataFrame(OpenDB(executesql([p1,p2,p3],[p4,p5,p6,p7]))).round(4)

    if result.empty:
        return jsonify({"result": ""})

    # DB 1/유클리드 거리 최댓값 1이상
    if result[6].max()>1:
        # 거리 1 이상인 애들만 유클리드 거리 평균/거리로 조정 왜하더라
        result['score1']=result[7].apply(lambda x:(sum(result[7])/5)/x if x>1 else x)
        # 1/유클리드거리가 1이상, 1이하 다있을때 = 유클리드 거리가 0 이상 실수
        if result[6].min()<1:
            result['score2']=result[6]*(result['score1'])
            maxs=1-result.loc[result[7]>1, 'score2'].max()
            print('---1이하', maxs)
        else:
            result['score2']=result[6]*(result['score1']+1)
            maxs=1-result[7].max()
            print('---모두 1이상', maxs)
        result.loc[result[7]<1, 'score2']=result.loc[result[7]<1, 7].apply(lambda x:1-x*maxs)
        result=result.drop([6,'score1'], axis=1)

    print(result.values.tolist())
    result=result.drop(7, axis=1)
    result=result.round(4).values.tolist()
    
    result[0].append(findURL(result[0][0]))
    
    return jsonify({"result": str(result)})

with open('activities.json', 'r', encoding='utf-8') as json_file:
    activities = json.load(json_file)

@app.route('/api/activities', methods=['GET'])
def receive_data_activity1():
    p1 = request.args.get('p1') # 실내외
    p2 = request.args.get('p2') # 도시 자연
    p3 = request.args.get('p3') # 하고싶은거
    p4 = request.args.get('p4') # 참여 휴식 관람
    
    input_tags=[p1,p2,p3,p4]
    print(input_tags)
    
    matching_activities = [activity for activity, tags in activities.items()
                            if (input_tags[0] == 'r' or input_tags[0] in tags["#1"] == input_tags[0]) and
                            (input_tags[1] == 'r' or tags["#4"] == input_tags[1]) and
                            (input_tags[2] == 'r' or tags["#2"] == input_tags[2]) and
                            (input_tags[3] == 'r' or tags["#3"] == input_tags[3])]
    

    
    return jsonify({"result": str(matching_activities) if len(matching_activities) else ""})

@app.route('/api/activity', methods=['GET'])
def receive_data_activity2():
    p1 = request.args.get('p1')
    print(p1)
    url = f'https://maps.googleapis.com/maps/api/place/textsearch/json?query=군산 {p1}&key=AIzaSyAkziK2WLmJFjH0XkLzbwYKtNJ1fUdPV20'

    response = requests.get(url)
    result = response.json()['results']
    
    li = []
    for i in result:
        li.append([i['name'], i['geometry']['location']['lat'], i['geometry']['location']['lng']])
        print([i['name'], i['geometry']['location']['lat'], i['geometry']['location']['lng']])
    random.shuffle(li)
    
    return jsonify({"result": str(li[:11])})

if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)
