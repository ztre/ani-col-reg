from app.services.series import SeriesInfo, extract_series_info


def test_kimetsu_no_yaiba_trilogy_shares_series_key() -> None:
    base = extract_series_info("鬼灭之刃")
    entertainment_district = extract_series_info("鬼灭之刃 游郭篇")
    swordsmith_village = extract_series_info("鬼灭之刃 刀匠村篇")

    assert {base.series_key, entertainment_district.series_key, swordsmith_village.series_key} == {"鬼灭之刃"}
    assert base.series_title == "鬼灭之刃"
    assert base.season_label is None
    assert entertainment_district.season_label == "游郭篇"
    assert swordsmith_village.season_label == "刀匠村篇"


def test_split_cour_suffix_merges_with_base() -> None:
    base = extract_series_info("無職轉生 ～到了異世界就拿出真本事～")
    second_half = extract_series_info("無職轉生 ～到了異世界就拿出真本事～ 後半部")

    # series_title 展示上可能差尾部波浪号（剥离路径会清理悬挂标点），分组以 key 为准
    assert second_half.series_key == base.series_key
    assert second_half.season_label == "後半部"
    assert base.season_label is None


def test_split_cour_suffix_variants() -> None:
    first_half = extract_series_info("作品名 前半")
    front = extract_series_info("作品名 前編")
    upper = extract_series_info("作品名 上巻")
    part2 = extract_series_info("BEASTARS FINAL SEASON Part 2")
    part2_lower = extract_series_info("BEASTARS FINAL SEASON part 2")

    assert first_half.season_label == "前半"
    assert front.season_label == "前編"
    assert upper.season_label == "上巻"
    assert part2.season_label == "Part 2"
    assert part2.series_key == part2_lower.series_key
    assert part2.series_key == "beastarsfinalseason"


def test_trailing_wave_dash_does_not_split_series() -> None:
    with_dash = extract_series_info("無職轉生 ～到了異世界就拿出真本事～")
    season2 = extract_series_info("無職轉生 ～到了異世界就拿出真本事～ 第二季")

    assert with_dash.series_key == season2.series_key


def test_combined_suffix_label_orders_season_before_split() -> None:
    """组合后缀展示顺序：先季数（第X季），再分段（第X季度/篇）。"""
    split_cour = extract_series_info("無職轉生 ～到了異世界就拿出真本事～ 第三季 第二季度")
    assert split_cour.season_label == "第三季 第二季度"

    season_with_arc = extract_series_info("作品名 4th season 喪失篇")
    assert season_with_arc.season_label == "4th season 喪失篇"


def test_violet_evergarden_titles_stay_independent() -> None:
    tv = extract_series_info("紫罗兰永恒花园")
    movie = extract_series_info("紫罗兰永恒花园 剧场版")
    side_story = extract_series_info("紫罗兰永恒花园 外传")

    assert tv.season_label is None
    assert movie.season_label is None
    assert side_story.season_label is None
    assert len({tv.series_key, movie.series_key, side_story.series_key}) == 3


def test_pure_suffix_title_falls_back_to_original() -> None:
    info = extract_series_info("第二季")

    assert info.series_title == "第二季"
    assert info.series_key == "第二季"
    assert info.season_label is None


def test_chinese_season_suffix_variants() -> None:
    spaced = extract_series_info("关于我转生变成史莱姆这档事 第二季")
    assert spaced.series_title == "关于我转生变成史莱姆这档事"
    assert spaced.season_label == "第二季"

    bracketed = extract_series_info("转生史莱姆（第2期）")
    assert bracketed.series_title == "转生史莱姆"
    assert bracketed.season_label == "第2期"

    part_marker = extract_series_info("亚人 第二部")
    assert part_marker.series_title == "亚人"
    assert part_marker.season_label == "第二部"

    mixed_chinese_numeral = extract_series_info("航海王 第十五季")
    assert mixed_chinese_numeral.series_title == "航海王"
    assert mixed_chinese_numeral.season_label == "第十五季"


def test_arc_suffix_variants() -> None:
    spaced = extract_series_info("鬼灭之刃 游郭篇")
    assert spaced.series_title == "鬼灭之刃"
    assert spaced.season_label == "游郭篇"

    overlord = extract_series_info("OVERLORD 圣王国篇")
    assert overlord.series_title == "OVERLORD"
    assert overlord.season_label == "圣王国篇"

    bracketed = extract_series_info("命运石之门（负荷领域篇）")
    assert bracketed.series_title == "命运石之门"
    assert bracketed.season_label == "负荷领域篇"

    no_separator = extract_series_info("鬼灭之刃游郭篇")
    assert no_separator.series_title == "鬼灭之刃游郭篇"
    assert no_separator.season_label is None


def test_english_season_suffix_variants() -> None:
    season = extract_series_info("Made in Abyss Season 2")
    assert season.series_title == "Made in Abyss"
    assert season.season_label == "Season 2"

    series = extract_series_info("Fargo Series 3")
    assert series.series_title == "Fargo"
    assert series.season_label == "Series 3"

    lowercased = extract_series_info("fate zero season 2")
    assert lowercased.series_title == "fate zero"
    assert lowercased.season_label == "season 2"

    with_hanging_punctuation = extract_series_info("Fate/Grand Order - Season 2")
    assert with_hanging_punctuation.series_title == "Fate/Grand Order"
    assert with_hanging_punctuation.season_label == "Season 2"


def test_s_prefixed_number_suffix_variants() -> None:
    lyco = extract_series_info("Lycoris Recoil S2")
    assert lyco.series_title == "Lycoris Recoil"
    assert lyco.season_label == "S2"

    oshi = extract_series_info("Oshi no Ko S3")
    assert oshi.series_title == "Oshi no Ko"
    assert oshi.season_label == "S3"


def test_roman_numeral_suffix_variants() -> None:
    classroom = extract_series_info("暗杀教室 II")
    assert classroom.series_title == "暗杀教室"
    assert classroom.season_label == "II"

    gate = extract_series_info("STEINS;GATE III")
    assert gate.series_title == "STEINS;GATE"
    assert gate.season_label == "III"

    lowercased = extract_series_info("monster ii")
    assert lowercased.series_title == "monster ii"
    assert lowercased.season_label is None


def test_trailing_number_suffix_variants() -> None:
    two_digits = extract_series_info("进击的巨人 2")
    assert two_digits.series_title == "进击的巨人"
    assert two_digits.season_label == "2"

    english = extract_series_info("Attack on Titan 25")
    assert english.series_title == "Attack on Titan"
    assert english.season_label == "25"

    remainder_too_short = extract_series_info("A 1")
    assert remainder_too_short.series_title == "A 1"
    assert remainder_too_short.season_label is None

    three_digits = extract_series_info("某测试番 123")
    assert three_digits.series_title == "某测试番 123"
    assert three_digits.season_label is None


def test_does_not_strip_non_season_titles() -> None:
    for title in ["22/7", "Fate/Grand Order", "Re:从零开始的异世界生活", "SSSS.GRIDMAN", "PSYCHO-PASS"]:
        info = extract_series_info(title)
        assert info.series_title == title
        assert info.season_label is None
        assert info.series_key


def test_empty_and_blank_titles_return_empty_series_info() -> None:
    for title in ["", "   ", "　"]:
        assert extract_series_info(title) == SeriesInfo(series_key="", series_title="", season_label=None)


def test_series_key_normalization_equivalence() -> None:
    assert extract_series_info("鬼灭之刃").series_key == extract_series_info("鬼灭之刃 ").series_key
    assert extract_series_info("鬼灭之刃").series_key == extract_series_info("鬼灭之刃　").series_key
    assert extract_series_info("Love Live!").series_key == extract_series_info("ＬＯＶＥ ＬＩＶＥ！").series_key
    assert extract_series_info("Love Live!").series_key == "lovelive"


def test_source_signature_is_stripped_before_season_rules() -> None:
    # 数据源标题带 " | YourAnimes" 签名尾巴：先清理签名，再剥离季度后缀。
    info = extract_series_info("Re：從零開始的異世界生活 4th season 喪失篇 | YourAnimes")
    assert info.series_title == "Re：從零開始的異世界生活"
    # 组合后缀循环剥离，label 按剥离顺序拼接（先命中的 "喪失篇" 规则在前）。
    assert "喪失篇" in info.season_label and "4th season" in info.season_label
    assert "youranimes" not in info.series_key

    plain = extract_series_info("拜託了偶像公主 | YourAnimes")
    assert plain.series_title == "拜託了偶像公主"
    assert plain.season_label is None
    assert plain.series_key == "拜託了偶像公主"


def test_ordinal_season_suffix() -> None:
    fourth = extract_series_info("Re：從零開始的異世界生活 4th season")
    assert fourth.series_title == "Re：從零開始的異世界生活"
    assert fourth.season_label == "4th season"

    second = extract_series_info("SPY×FAMILY 2nd Season")
    assert second.series_title == "SPY×FAMILY"
    assert second.season_label == "2nd Season"


def test_chinese_quarter_suffix() -> None:
    info = extract_series_info("Dr.STONE 新石紀 SCIENCE FUTURE 第三季度 | YourAnimes")
    assert info.series_title == "Dr.STONE 新石紀 SCIENCE FUTURE"
    assert info.season_label == "第三季度"
