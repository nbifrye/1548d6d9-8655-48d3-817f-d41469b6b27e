---
layout: page
title: "このブログについて"
permalink: /about/
---

このブログは、デジタルアイデンティティ、認証、認可、アクセスコントロール、API セキュリティ、identity provisioning に関する標準仕様を日本語で整理します。

## 記事の考え方

1記事で仕様書全体を網羅することを目的にはしません。各記事ごとに対象読者と中心テーマを決め、「誰に、何を理解してもらう記事か」を明確にしてから執筆します。

記事は主に次の種類に分けます。

- 仕様や機能群の関係を説明する **Overview**
- protocol や ceremony の順序を説明する **Flow**
- 特定の規範要件を整理する **Requirement**
- 標準仕様が規定する攻撃対策を扱う **Security Practice**
- extension や token など1要素を扱う **Feature Deep Dive**
- 公式の revision history に基づく **Version Difference**

各記事の冒頭には「対象読者」「この記事で伝えること」「扱わないこと」を明記します。

## 情報源

技術的事実の根拠には、IETF / RFC Editor、OpenID Foundation、W3C、OASIS など、仕様策定主体が公開する一次資料を使用します。二次資料やベンダーブログは、標準仕様上の事実を確定する根拠として使用しません。

## 記述方針

MUST / SHOULD / MAY などの規範語は、原文の強度を変更せずに記載します。仕様にない推奨、評価、見解は追加しません。仕様が実装者や deployment の local policy に判断を委ねている箇所では、その事実のみを記載します。

Protocol や processing sequence がある記事には、記事テーマに対応した Mermaid 図を掲載します。

## 文書ステータス

RFC、BCP、W3C Recommendation、Candidate Recommendation、OpenID Final Specification、Implementer's Draft、Internet-Draft などの status を区別し、発行日または最終確認日を記載します。
