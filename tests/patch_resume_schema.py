with open('app/schema/resume.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = '''        if isinstance(data, dict):
            if "skills" not in data:
                user_id = data.pop("user_id", None)
                is_orig = data.pop("is_original", False)
                return {"skills": data, "user_id": user_id, "is_original": is_orig}
        return data'''

replacement = '''        if isinstance(data, dict):
            if "skills" not in data:
                user_id = data.pop("user_id", None)
                is_orig = data.pop("is_original", False)
                return {"skills": data, "user_id": user_id, "is_original": is_orig}
            elif isinstance(data.get("skills"), dict) and "skills" in data["skills"] and len(data["skills"]) == 1:
                # Unwrap nested {"skills": {"skills": {...}}}
                data["skills"] = data["skills"]["skills"]
        return data'''

if target in content:
    content = content.replace(target, replacement)
    with open('app/schema/resume.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("app/schema/resume.py updated successfully.")
else:
    print("Target not found.")


