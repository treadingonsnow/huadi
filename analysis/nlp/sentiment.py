# 情感分析模块
# 功能：
# - analyze_sentiment()           单条评论情感分析（使用SnowNLP，返回情感得分 0-1）
# - batch_analyze_sentiment()     批量评论情感分析
# - classify_sentiment()          情感分类（正面/中性/负面，阈值：>0.6正面，<0.4负面）
# - analyze_aspect_sentiment()    方面级情感分析（分别分析口味、环境、服务的情感倾向）
#                                  基于 config/dictionaries/sentiment_dict.py 关键词匹配
# 依赖：snownlp, jieba
