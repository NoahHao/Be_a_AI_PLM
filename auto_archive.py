#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件自动归档和规则提取工具

功能：
1. 扫描当前目录下所有文件，找出以 `_完成.md` 结尾的文件
2. 将这些文件复制到 `0.已经完成/` 目录
3. 从 `0.已经完成/` 目录的文件中提取 `--Rule` 和 `--话术` 标志之间的内容
4. 将提取的内容添加到 `Skill.md` 文件中，分别保存到 "# 行为规则" 和 "# 话术" 部分
5. 检查已处理的文件和重复内容，避免重复更新
"""

import os
import re
import shutil
import hashlib
from pathlib import Path


class FileArchiver:
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.completed_dir = self.base_dir / "0.已经完成"
        self.skill_file = self.base_dir / "Skill.md"
        self.processed_file = self.completed_dir / ".processed_files"
        self.file_hashes = self._load_processed_hashes()

    def _load_processed_hashes(self):
        """加载已处理的文件指纹"""
        if self.processed_file.exists():
            try:
                with open(self.processed_file, 'r', encoding='utf-8') as f:
                    return set(line.strip() for line in f if line.strip())
            except Exception as e:
                print(f"[!] 读取已处理文件记录时出错: {e}")
        return set()

    def _get_file_hash(self, file_path):
        """生成文件的哈希值（用于去重）"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            # 如果读取失败，使用文件名作为后备
            return hashlib.md5(str(file_path).encode()).hexdigest()

    def find_completed_files(self):
        """查找所有以 `_完成.md` 结尾的文件"""
        completed_files = []
        for root, _, files in os.walk(self.base_dir):
            for file in files:
                if file.endswith("_完成.md"):
                    file_path = Path(root) / file
                    completed_files.append(file_path)
        return completed_files

    def move_to_completed(self, file_path):
        """将文件复制到已完成目录"""
        if not self.completed_dir.exists():
            self.completed_dir.mkdir(parents=True)
            print(f"[OK] 创建目录: {self.completed_dir}")

        target_path = self.completed_dir / file_path.name
        try:
            shutil.copy2(str(file_path), str(target_path))

            # 记录已处理的文件
            file_hash = self._get_file_hash(target_path)
            self.file_hashes.add(file_hash)
            self._save_processed_hashes()

            print(f"[OK] 复制文件: {file_path.name} -> {self.completed_dir}")
        except PermissionError:
            print(f"[!] 文件 {file_path.name} 正在使用中，跳过复制")
        except Exception as e:
            print(f"[!] 复制文件 {file_path.name} 失败: {e}")

    def _save_processed_hashes(self):
        """保存已处理的文件指纹"""
        try:
            with open(self.processed_file, 'w', encoding='utf-8') as f:
                for hash_val in self.file_hashes:
                    f.write(hash_val + '\n')
        except Exception as e:
            print(f"[!] 保存已处理文件记录时出错: {e}")

    def extract_rules(self):
        """从已完成目录的文件中提取 `--Rule` 和 `--话术` 之间的内容"""
        rules = []
        scripts = []

        if not self.completed_dir.exists():
            print("[!] 已完成目录不存在，跳过提取")
            return rules, scripts

        rule_pattern = r'--Rule\s*(.*?)--Rule'
        script_pattern = r'--话术\s*(.*?)--话术'

        file_count = 0

        for file_path in self.completed_dir.glob("*.md"):
            file_count += 1
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                    # 提取规则
                    rule_matches = re.findall(rule_pattern, content, re.DOTALL)
                    for match in rule_matches:
                        cleaned = match.strip()
                        cleaned = re.sub(r'\n\s*\n', '\n', cleaned)
                        if cleaned and cleaned not in rules:
                            rules.append(cleaned)

                    # 提取话术
                    script_matches = re.findall(script_pattern, content, re.DOTALL)
                    for match in script_matches:
                        cleaned = match.strip()
                        cleaned = re.sub(r'\n\s*\n', '\n', cleaned)
                        if cleaned and cleaned not in scripts:
                            scripts.append(cleaned)

            except Exception as e:
                print(f"[!] 读取文件 {file_path.name} 时出错: {e}")

        print(f"[OK] 扫描 {file_count} 个文件，找到 {len(rules)} 条规则，{len(scripts)} 条话术")
        return rules, scripts

    def update_skill_file(self, rules, scripts):
        """更新 Skill.md 文件，包含规则和话术（只添加新的）"""
        # 准备规则内容
        rule_lines = ["# 行为规则\n", ""]

        # 按出现顺序编号
        for idx, rule in enumerate(rules, 1):
            rule = rule.strip()
            if rule:
                rule_lines.append(f"{idx}. **Rule {idx} ：{rule}**")
                rule_lines.append("")

        # 准备话术内容
        script_lines = ["# 话术\n", ""]

        # 按出现顺序编号
        for idx, script in enumerate(scripts, 1):
            script = script.strip()
            if script:
                script_lines.append(f"{idx}. **话术 {idx} ：{script}**")
                script_lines.append("")

        # 检查文件是否存在
        if self.skill_file.exists():
            try:
                with open(self.skill_file, 'r', encoding='utf-8') as f:
                    existing_content = f.read()

                # 检查是否已有 "# 行为规则" 和 "# 话术" 部分
                rule_header_pos = existing_content.find("# 行为规则")
                script_header_pos = existing_content.find("# 话术")

                # 如果已有这些部分，先提取现有内容用于去重
                existing_rules = []
                existing_scripts = []

                if rule_header_pos != -1:
                    content_start = rule_header_pos + len("# 行为规则")
                    next_header = existing_content.find('\n#', content_start)
                    if next_header == -1:
                        next_header = len(existing_content)

                    existing_section = existing_content[content_start:next_header]
                    existing_rules = re.findall(r'\*\*Rule \d+ ：(.+?)\*\*', existing_section)

                if script_header_pos != -1:
                    content_start = script_header_pos + len("# 话术")
                    next_header = existing_content.find('\n#', content_start)
                    if next_header == -1:
                        next_header = len(existing_content)

                    existing_section = existing_content[content_start:next_header]
                    existing_scripts = re.findall(r'\*\*话术 \d+ ：(.+?)\*\*', existing_section)

                # 检查是否有新内容需要添加
                new_rules = [rule for rule in rules if rule not in existing_rules]
                new_scripts = [script for script in scripts if script not in existing_scripts]

                if not new_rules and not new_scripts:
                    print(f"[SKIP] 没有新内容需要添加，Skill.md 已是最新状态")
                    return

                # 替换规则内容（只替换新规则）
                if rule_header_pos != -1 and new_rules:
                    content_start = rule_header_pos + len("# 行为规则")
                    next_header = existing_content.find('\n#', content_start)
                    if next_header == -1:
                        next_header = len(existing_content)

                    # 获取现有的规则编号范围
                    existing_rule_numbers = set()
                    if existing_rules:
                        existing_rule_numbers = {
                            int(re.search(r'\d+', rule).group())
                            for rule in existing_rules
                        }

                    # 生成新的规则编号
                    next_rule_num = max(existing_rule_numbers) + 1 if existing_rule_numbers else 1

                    # 添加新规则
                    new_rule_lines = []
                    for rule in new_rules:
                        new_rule_lines.append(f"{next_rule_num}. **Rule {next_rule_num} ：{rule}**")
                        new_rule_lines.append("")
                        next_rule_num += 1

                    existing_content = (
                        existing_content[:content_start] +
                        '\n'.join(new_rule_lines) +
                        existing_content[next_header:]
                    )

                # 替换话术内容（只替换新话术）
                if script_header_pos != -1 and new_scripts:
                    content_start = script_header_pos + len("# 话术")
                    next_header = existing_content.find('\n#', content_start)
                    if next_header == -1:
                        next_header = len(existing_content)

                    # 获取现有的话术编号范围
                    existing_script_numbers = set()
                    if existing_scripts:
                        existing_script_numbers = {
                            int(re.search(r'\d+', script).group())
                            for script in existing_scripts
                        }

                    # 生成新的话术编号
                    next_script_num = max(existing_script_numbers) + 1 if existing_script_numbers else 1

                    # 添加新话术
                    new_script_lines = []
                    for script in new_scripts:
                        new_script_lines.append(f"{next_script_num}. **话术 {next_script_num} ：{script}**")
                        new_script_lines.append("")
                        next_script_num += 1

                    existing_content = (
                        existing_content[:content_start] +
                        '\n'.join(new_script_lines) +
                        existing_content[next_header:]
                    )

                    # 如果规则部分也存在于话术部分之后，需要重新找到规则部分
                    rule_header_pos = existing_content.find("# 行为规则")
                    if rule_header_pos != -1 and new_rules:
                        rule_next_header = existing_content.find('\n#', rule_header_pos + len("# 行为规则"))
                        if rule_next_header == -1:
                            rule_next_header = len(existing_content)

                        # 获取现有的规则编号范围
                        existing_rule_numbers = set()
                        if existing_rules:
                            existing_rule_numbers = {
                                int(re.search(r'\d+', rule).group())
                                for rule in existing_rules
                            }

                        # 生成新的规则编号
                        next_rule_num = max(existing_rule_numbers) + 1 if existing_rule_numbers else 1

                        # 添加新规则
                        new_rule_lines = []
                        for rule in new_rules:
                            new_rule_lines.append(f"{next_rule_num}. **Rule {next_rule_num} ：{rule}**")
                            new_rule_lines.append("")
                            next_rule_num += 1

                        existing_content = (
                            existing_content[:rule_header_pos + len("# 行为规则")] +
                            '\n'.join(new_rule_lines) +
                            existing_content[rule_next_header:]
                        )

                # 写回文件
                with open(self.skill_file, 'w', encoding='utf-8') as f:
                    f.write(existing_content)

                print(f"[OK] 更新 Skill.md，添加 {len(new_rules)} 条新规则，{len(new_scripts)} 条新话术")

            except Exception as e:
                print(f"[!] 更新 Skill.md 时出错: {e}")
        else:
            # 创建新文件
            with open(self.skill_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(rule_lines + [""] + script_lines))
            print(f"[OK] 创建新 Skill.md，添加 {len(rules)} 条规则，{len(scripts)} 条话术")

        # 检查文件是否存在
        if self.skill_file.exists():
            try:
                with open(self.skill_file, 'r', encoding='utf-8') as f:
                    existing_content = f.read()

                # 检查是否已有 "# 行为规则" 和 "# 话术" 部分
                rule_header_pos = existing_content.find("# 行为规则")
                script_header_pos = existing_content.find("# 话术")

                # 替换规则内容
                if rule_header_pos != -1:
                    content_start = rule_header_pos + len("# 行为规则")
                    next_header = existing_content.find('\n#', content_start)
                    if next_header == -1:
                        next_header = len(existing_content)

                    existing_content = (
                        existing_content[:content_start] +
                        '\n'.join(rule_lines) +
                        existing_content[next_header:]
                    )

                # 替换话术内容
                if script_header_pos != -1:
                    content_start = script_header_pos + len("# 话术")
                    next_header = existing_content.find('\n#', content_start)
                    if next_header == -1:
                        next_header = len(existing_content)

                    existing_content = (
                        existing_content[:content_start] +
                        '\n'.join(script_lines) +
                        existing_content[next_header:]
                    )

                    # 如果规则部分也存在于话术部分之后，需要重新找到规则部分
                    rule_header_pos = existing_content.find("# 行为规则")
                    if rule_header_pos != -1:
                        rule_next_header = existing_content.find('\n#', rule_header_pos + len("# 行为规则"))
                        if rule_next_header == -1:
                            rule_next_header = len(existing_content)

                        existing_content = (
                            existing_content[:rule_header_pos + len("# 行为规则")] +
                            '\n'.join(rule_lines) +
                            existing_content[rule_next_header:]
                        )

                # 写回文件
                with open(self.skill_file, 'w', encoding='utf-8') as f:
                    f.write(existing_content)

                print(f"[OK] 更新现有 Skill.md，添加 {len(rules)} 条规则，{len(scripts)} 条话术")

            except Exception as e:
                print(f"[!] 更新 Skill.md 时出错: {e}")
        else:
            # 创建新文件
            with open(self.skill_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(rule_lines + [""] + script_lines))
            print(f"[OK] 创建新 Skill.md，添加 {len(rules)} 条规则，{len(scripts)} 条话术")

    def run(self):
        """执行完整流程"""
        print("=" * 60)
        print("开始执行文件归档和规则提取")
        print("=" * 60)

        # 步骤 1: 查找已完成文件
        print("\n[步骤 1] 查找已完成文件...")
        completed_files = self.find_completed_files()

        if not completed_files:
            print("[!] 没有找到已完成文件")
        else:
            print(f"[OK] 找到 {len(completed_files)} 个已完成文件:")
            for file_path in completed_files:
                print(f"  - {file_path.name}")

            # 步骤 2: 移动文件
            print(f"\n[步骤 2] 移动文件到已完成目录...")
            for file_path in completed_files:
                self.move_to_completed(file_path)

        # 步骤 3: 提取规则和话术
        print(f"\n[步骤 3] 从已完成文件中提取规则和话术...")
        rules, scripts = self.extract_rules()

        # 步骤 4: 更新 Skill.md
        print(f"\n[步骤 4] 更新 Skill.md...")
        self.update_skill_file(rules, scripts)

        print("\n" + "=" * 60)
        print("Execution completed!")
        print("=" * 60)


def main():
    # 获取脚本所在目录
    script_dir = Path(__file__).parent.absolute()

    # 创建归档器并执行
    archiver = FileArchiver(script_dir)
    archiver.run()


if __name__ == "__main__":
    main()
