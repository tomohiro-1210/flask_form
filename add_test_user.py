from app import User, db

# db.drop_all()
# db.create_all()

# インスタンス生成
user1 = User("admin_mimic@mimic.com", "Mimic Admin User", "3309", "1")
user2 = User("hitokui@mimic.com", "Hitokui User", "19185", "0")
user3 = User("padora@mimic.com", "Pandora User", "pandora", "0")
db.session.add_all([user1, user2, user3])
db.session.commit()

user_list = []
for i in range(101):
    user_list.append(User(f"seeder_user{i}@seeder.com", f"Seeder Usr{i}", f"{i}{i}{i}", "0"))


db.session.add_all(user_list)
db.session.commit()

