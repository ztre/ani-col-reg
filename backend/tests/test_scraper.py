from pathlib import Path

from app.services.mikan import extract_bangumi_subject_url, merge_detail_records, parse_bangumi_detail_html, parse_mikan_cover_html, parse_mikan_detail_html, parse_mikan_season_html
from app.services.scraper import AnimeSourceRecord, parse_detail_html, parse_season_html, season_url


def test_season_url_uses_bangumi_path() -> None:
    assert season_url("https://youranimes.tw", 2026, 2) == "https://youranimes.tw/bangumi/202604"


def test_parse_season_html_fixture() -> None:
    html = Path("tests/fixtures/youranimes_season.html").read_text(encoding="utf-8")

    records = parse_season_html(html, "https://youranimes.tw", 2026, 2)

    assert len(records) == 2
    assert records[0].title_cn == "春日测试番"
    assert records[0].source_id == "alpha"
    assert records[0].source_url == "https://youranimes.tw/animes/alpha"
    assert records[0].cover_url == "https://cdn.example.test/alpha.webp"
    assert records[0].year == 2026
    assert records[0].season == 2
    assert records[1].cover_url == "https://youranimes.tw/images/beta.jpg"


def test_parse_mikan_cover_html_fixture() -> None:
    html = Path("tests/fixtures/mikan_cover_flow.html").read_text(encoding="utf-8")

    covers = parse_mikan_cover_html(html, "https://mikanani.me")

    assert len(covers) == 2
    assert covers[0].title == "春日测试番"
    assert covers[0].cover_url == "https://mikanani.me/images/Bangumi/alpha.jpg"


def test_parse_youranimes_detail_html_extracts_detail_sections() -> None:
        html = """
        <html>
            <head>
                <meta property="og:title" content="春日测试番">
                <meta property="og:image" content="https://cdn.example.test/detail-alpha.webp">
            </head>
            <body>
                <h1>春日测试番</h1>
                <p>首映日期為 2026-04-01</p>
                <section>
                    <h2>簡介</h2>
                    <p>这是详情页里的正式简介。</p>
                </section>
                <section>
                    <h2>作品元素</h2>
                    <a href="/tags/fantasy">奇幻(1)</a>
                    <a href="/tags/action">动作(2)</a>
                </section>
                <section>
                    <h2>宣傳影片</h2>
                    <a href="https://www.youtube.com/watch?v=alpha">PV</a>
                </section>
                <section>
                    <h2>製作陣容</h2>
                    <p>動畫制作：Example Studio</p>
                </section>
                <section>
                    <h2>登場角色 / 演出聲優</h2>
                    <p>主角：声优 A</p>
                </section>
            </body>
        </html>
        """

        record = parse_detail_html(
                html,
                "https://youranimes.tw",
                "https://youranimes.tw/animes/alpha",
                fallback=AnimeSourceRecord(title_cn="春日测试番", source_id="alpha", source_url=None, year=2026, season=2),
        )

        assert record.synopsis == "这是详情页里的正式简介。"
        assert record.staff == "動畫制作：Example Studio"
        assert record.cast == "主角：声优 A"
        assert record.tags == "奇幻, 动作"
        assert record.pv_url == "https://www.youtube.com/watch?v=alpha"
        assert record.premiere_date == "2026-04-01"
        assert record.cover_url == "https://cdn.example.test/detail-alpha.webp"


def test_parse_mikan_season_html_fixture() -> None:
        html = Path("tests/fixtures/mikan_cover_flow.html").read_text(encoding="utf-8")

        records = parse_mikan_season_html(html, "https://mikanani.me", 2026, 2)

        assert len(records) == 2
        assert records[0].source_url == "https://mikanani.me/Home/Bangumi/123"
        assert records[0].source_id == "123"
        assert records[0].cover_url == "https://mikanani.me/images/Bangumi/alpha.jpg"


def test_parse_mikan_detail_html_extracts_synopsis_and_date() -> None:
    html = """
    <html>
        <head>
        </head>
        <body>
            <div class="bangumi-title">哆啦A梦</div>
            <div class="bangumi-poster"><img src="/images/Bangumi/681.jpg"></div>
            <div class="bangumi-info">放送日期：星期五</div>
            <div class="bangumi-info">总集数：放送中</div>
            <div class="bangumi-info">放送开始：4/15/2005</div>
            <div class="header2"><span class="header2-text">概况介绍</span></div>
            <p class="header2-desc">这是 Mikan 的番组概况介绍。 [简介原文] Japanese text</p>
            <a href="https://bgm.tv/subject/681">Bangumi</a>
        </body>
    </html>
    """

    record = parse_mikan_detail_html(
        html,
        "https://mikanani.me",
        "https://mikanani.me/Home/Bangumi/681",
        fallback=AnimeSourceRecord(title_cn="哆啦A梦", source_id="681", source_url=None, year=2026, season=2),
    )

    assert record.title_cn == "哆啦A梦"
    assert record.synopsis == "这是 Mikan 的番组概况介绍。"
    assert record.premiere_date == "4/15/2005"
    assert record.cover_url == "https://mikanani.me/images/Bangumi/681.jpg"
    assert extract_bangumi_subject_url(html) == "https://bgm.tv/subject/681"


def test_parse_mikan_detail_html_prefers_poster_background_over_placeholder_image() -> None:
    html = """
    <html>
        <body>
            <div class="bangumi-title">吉伊卡哇</div>
            <div class="bangumi-poster" style="background-image: url('/images/Bangumi/202204/d8ef46c0.jpg?width=400&amp;height=560&amp;format=webp');"></div>
            <img src="/images/mikan-pic.png">
        </body>
    </html>
    """

    record = parse_mikan_detail_html(
        html,
        "https://mikanani.me",
        "https://mikanani.me/Home/Bangumi/3288",
        fallback=AnimeSourceRecord(title_cn="吉伊卡哇", source_id="3288", source_url=None, year=2026, season=2),
    )

    assert record.cover_url == "https://mikanani.me/images/Bangumi/202204/d8ef46c0.jpg?width=400&height=560&format=webp"


def test_parse_bangumi_detail_html_extracts_rich_fields() -> None:
    html = """
    <html>
        <body>
            <div id="headerSubject"><h1><a class="nameSingle">Re:ゼロから始める異世界生活 4th season 喪失編</a></h1></div>
            <div id="bangumiInfo"><a class="cover" href="/subject/547888"><img src="/pic/cover/l/12/34/example.jpg"></a></div>
            <div id="subject_summary">这是 Bangumi 里的详细简介。</div>
            <ul id="infobox">
                <li><span class="tip">中文名: </span>Re：从零开始的异世界生活 第四季 丧失篇</li>
                <li><span class="tip">别名: </span>Re: Zero S4</li>
                <li><span class="tip">放送开始: </span>2026年4月8日</li>
                <li><span class="tip">动画制作: </span>WHITE FOX</li>
                <li><span class="tip">导演: </span>篠原正寛</li>
                <li><span class="tip">音乐: </span>末廣健一郎</li>
            </ul>
            <div class="subject_tag_section"><div class="inner">
                <a>TV 388</a><a>奇幻 439</a><a>异世界 221</a>
            </div></div>
            <ul id="browserItemList">
                <li class="item">ナツキ・スバル 主角 (+170) CV 小林裕介</li>
                <li class="item">エミリア 主角 (+185) CV 高橋李依</li>
            </ul>
        </body>
    </html>
    """

    record = parse_bangumi_detail_html(
        html,
        "https://bgm.tv/subject/547888",
        fallback=AnimeSourceRecord(title_cn="回退标题", source_id="681", source_url="https://mikanani.me/Home/Bangumi/681", year=2026, season=2),
    )

    assert record.title_cn == "Re：从零开始的异世界生活 第四季 丧失篇"
    assert record.title_jp == "Re:ゼロから始める異世界生活 4th season 喪失編"
    assert record.aliases == "Re: Zero S4"
    assert record.synopsis == "这是 Bangumi 里的详细简介。"
    assert record.premiere_date == "2026-04-08"
    assert record.platforms == "TV"
    assert record.staff == "动画制作: WHITE FOX；导演: 篠原正寛；音乐: 末廣健一郎"
    assert "CV 小林裕介" in (record.cast or "")
    assert record.tags == "TV, 奇幻, 异世界"
    assert record.cover_url == "https://bgm.tv/pic/cover/l/12/34/example.jpg"


def test_merge_detail_records_prefers_primary_and_fills_missing_fields() -> None:
    primary = AnimeSourceRecord(
        title_cn="主记录",
        source_id="1",
        source_url="https://mikanani.me/Home/Bangumi/1",
        year=2026,
        season=2,
        synopsis="主简介",
        cover_url="https://mikanani.me/images/a.jpg",
    )
    supplement = AnimeSourceRecord(
        title_cn="补充记录",
        source_id="2",
        source_url="https://bgm.tv/subject/2",
        year=2026,
        season=2,
        staff="制作：Example",
        cast="角色：声优",
        tags="奇幻",
    )

    merged = merge_detail_records(primary, supplement)

    assert merged.title_cn == "主记录"
    assert merged.synopsis == "主简介"
    assert merged.cover_url == "https://mikanani.me/images/a.jpg"
    assert merged.staff == "制作：Example"
    assert merged.cast == "角色：声优"
    assert merged.tags == "奇幻"


def test_merge_detail_records_uses_supplement_cover_when_primary_is_placeholder() -> None:
    primary = AnimeSourceRecord(
        title_cn="吉伊卡哇",
        source_id="3288",
        source_url="https://mikanani.me/Home/Bangumi/3288",
        year=2026,
        season=2,
        cover_url="https://mikanani.me/images/mikan-pic.png",
    )
    supplement = AnimeSourceRecord(
        title_cn="吉伊卡哇",
        source_id="3288",
        source_url="https://mikanani.me/Home/Bangumi/3288",
        year=2026,
        season=2,
        cover_url="https://bgm.tv/pic/cover/l/c9/b1/354700_S6YP6.jpg",
    )

    merged = merge_detail_records(primary, supplement)

    assert merged.cover_url == "https://bgm.tv/pic/cover/l/c9/b1/354700_S6YP6.jpg"
