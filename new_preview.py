        # 응답용 아이템 변환 (calculate_quote에서 이미 QuoteItemOutput 반환)
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
        ]
        
        return QuotePreviewResponse(totals=totals, items=output_items)