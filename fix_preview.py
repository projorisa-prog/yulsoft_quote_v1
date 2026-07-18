with open('app/routers/public_quotes.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = '''        # 응답용 아이템 변환
        output_items = [
            QuoteItemOutput(
                area=item.area,
                task=item.task,
                days=item.days,
                qty=item.qty,
                unit_price=item.unit_price,
                total_price=item.total_price,
                exclude_area=item.exclude_area,
                memo=item.memo
            ) for item in items
        ]'''

new = '''        # 응답용 아이템 변환 (calculate_quote에서 이미 QuoteItemOutput 반환)
        output_items = [
            QuoteItemOutput(
                area=item.area,
                task=item.task,
                days=item.days,
                qty=item.qty,
                unit_price=item.unit_price,
                total_price=item.total_price,
                exclude_area=item.exclude_area,
                memo=item.memo,
                id=item.id,
                sort_order=item.sort_order
            ) for item in items
        ]'''

content = content.replace(old, new)

with open('app/routers/public_quotes.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed')