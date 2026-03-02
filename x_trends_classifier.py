import boto3, json

bedrock = boto3.client('bedrock-runtime')

SYSTEM_PROMPT = """あなたはソーシャルメディアのトレンド分類の専門家です。
入力されたトレンド情報を以下のカテゴリに分類してください。

【カテゴリ一覧】
- NATURAL_DISASTER: 地震、台風、洪水、火山、山火事、津波
- PRODUCT_REVIEW: 製品評価、新製品、リコール、サービス評判
- POLITICS: 選挙、政策、外交、社会運動、法律
- ECONOMY: 株式、為替、物価、企業決算、M&A
- TECH: AI、新技術、データ漏洩、科学発見
- ENTERTAINMENT: 映画、音楽、ゲーム、芸能人
- SPORTS: スポーツ試合、選手、大会結果
- HEALTH: 感染症、新薬、公衆衛生、医療政策
- OTHER: 上記に該当しないもの

必ず以下のJSON形式のみで回答してください:
{
  "category": "カテゴリ名",
  "sub_topic": "具体的なサブトピック",
  "sentiment": "positive|negative|neutral|mixed",
  "region": "関連する地域（不明ならnull）",
  "summary": "1文の日本語要約",
  "confidence": 0.0-1.0
}"""

def classify_trend(text: str) -> dict:
    resp = bedrock.invoke_model(
        modelId='anthropic.claude-3-5-haiku-20241022-v1:0',
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 200,
            "system": SYSTEM_PROMPT,
            "messages": [
                {"role": "user",
                 "content": f"以下のトレンドを分類:\n{text}"}
            ]
        })
    )
    body = json.loads(resp['body'].read())
    return json.loads(body['content'][0]['text'])

# ========== 使用例 ==========
trends = [
    "東京で震度5の地震が発生、津波の心配なし",
    "iPhone 16 Proのカメラ性能レビューが話題に",
    "日経平均が3万8000円台を回復",
    "大谷翔平が50本目のホームラン達成",
]

for t in trends:
    result = classify_trend(t)
    print(f"{t}")
    print(f"  → {result['category']} | {result['summary']}")
    print(f"  → 感情: {result['sentiment']} "
          f"| 信頼度: {result['confidence']}")
    print()

# ========== 批量处理 + DynamoDB 保存 ==========
import time
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('XTrendsClassified')

def batch_classify_and_store(trends: list):
    for t in trends:
        result = classify_trend(t['text'])
        result['trend_id'] = t['id']
        result['raw_text'] = t['text']
        result['timestamp'] = int(time.time())
        table.put_item(Item=result)
        time.sleep(0.1)  # 速率制限対策