from app import User, db

# db.drop_all()
db.create_all()

# インスタンス生成
user1 = User("admin_mimic@mimic.com", "Mimic Admin User", "3309", "1")
user2 = User("hitokui@mimic.com", "Hitokui User", "19185", "0")
user3 = User("padora@mimic.com", "Pandora User", "pandora", "0")

# データ追加（リストでまとめる）
db.session.add_all([user1, user2, user3])
db.session.commit()

# IDの出力
print(user1.id)
print(user2.id)
print(user3.id)
