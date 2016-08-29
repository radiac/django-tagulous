/*
** Jasmine tests for tagulous.js
** Port of python UtilsTest test case
*/
describe("Tagulous.parseTags", function () {
    it("parses tags with commas", function () {
        var tags = Tagulous.parseTags('adam,brian,chris');
        expect(tags.length).toBe(3);
        expect(tags[0]).toBe('adam');
        expect(tags[1]).toBe('brian');
        expect(tags[2]).toBe('chris');
    });

    it("parses tags with spaces", function () {
        var tags = Tagulous.parseTags('adam brian chris');
        expect(tags.length).toBe(3);
        expect(tags[0]).toBe('adam');
        expect(tags[1]).toBe('brian');
        expect(tags[2]).toBe('chris');
    });

    it("parses tags with commas before spaces", function () {
        var tags = Tagulous.parseTags('adam, brian chris');
        expect(tags.length).toBe(2);
        expect(tags[0]).toBe('adam');
        expect(tags[1]).toBe('brian chris');
    });

    it("parses tags with commas after spaces", function () {
        var tags = Tagulous.parseTags('adam brian  ,  chris');
        expect(tags.length).toBe(2);
        expect(tags[0]).toBe('adam brian');
        expect(tags[1]).toBe('chris');
    });

    it("sorts tags into order", function () {
        var tags = Tagulous.parseTags('chris, adam, brian');
        expect(tags.length).toBe(3);
        expect(tags[0]).toBe('adam');
        expect(tags[1]).toBe('brian');
        expect(tags[2]).toBe('chris');
    });

    it("parses tags with quotes", function () {
        var tags = Tagulous.parseTags('"adam, one"');
        expect(tags.length).toBe(1);
        expect(tags[0]).toBe('adam, one');
    });

    it("parses tags with quotes and comma delimiter", function () {
        var tags = Tagulous.parseTags('"adam, one","brian, two","chris, three"');
        expect(tags.length).toBe(3);
        expect(tags[0]).toBe('adam, one');
        expect(tags[1]).toBe('brian, two');
        expect(tags[2]).toBe('chris, three');
    });

    it("parses tags with quotes and space delimiter", function () {
        var tags = Tagulous.parseTags('"adam one" "brian two" "chris three"');
        expect(tags.length).toBe(3);
        expect(tags[0]).toBe('adam one');
        expect(tags[1]).toBe('brian two');
        expect(tags[2]).toBe('chris three');
    });

    it("parses tags with quotes and comma delimiter, ignoring adjacent spaces", function () {
        var tags = Tagulous.parseTags('"adam, one"  ,  "brian, two"  ,  "chris, three"');
        expect(tags.length).toBe(3);
        expect(tags[0]).toBe('adam, one');
        expect(tags[1]).toBe('brian, two');
        expect(tags[2]).toBe('chris, three');
    });

    it("parses tags with quotes and comma delimiter before space", function () {
        var tags = Tagulous.parseTags('"adam one","brian two" "chris three"');
        expect(tags.length).toBe(2);
        expect(tags[0]).toBe('adam one');
        expect(tags[1]).toBe('brian two" "chris three');
    });

    it("parses tags with quotes and comma delimiter after space", function () {
        var tags = Tagulous.parseTags('"adam one" "brian two","chris three"');
        expect(tags.length).toBe(2);
        expect(tags[0]).toBe('adam one" "brian two');
        expect(tags[1]).toBe('chris three');
    });

    it("parses tags with quotes inside tags - quotes don't delimit", function () {
        var tags = Tagulous.parseTags('adam"brian,chris dave');
        expect(tags.length).toBe(2);
        expect(tags[0]).toBe('adam"brian');
        expect(tags[1]).toBe('chris dave');
    });

    it("parses tags with quotes which don't close", function () {
        var tags = Tagulous.parseTags('"adam,one","brian,two","chris, dave');
        expect(tags.length).toBe(3);
        // Will be sorted, so " comes first
        expect(tags[0]).toBe('"chris, dave');
        expect(tags[1]).toBe('adam,one');
        expect(tags[2]).toBe('brian,two');
    });

    it("parses tags with mix of quotes and no quotes", function () {
        var tags = Tagulous.parseTags('adam , "brian, chris" , dave');
        expect(tags.length).toBe(3);
        expect(tags[0]).toBe('adam');
        expect(tags[1]).toBe('brian, chris');
        expect(tags[2]).toBe('dave');
    });

    it("parses tags with mix of quotes and no quotes sorted in order", function () {
        var tags = Tagulous.parseTags('chris, "adam", brian');
        expect(tags.length).toBe(3);
        expect(tags[0]).toBe('adam');
        expect(tags[1]).toBe('brian');
        expect(tags[2]).toBe('chris');
    });

    it("parses tags with escaped quotes", function () {
        var tags = Tagulous.parseTags('adam, br""ian, ""chris, dave""');
        expect(tags.length).toBe(4);
        expect(tags[0]).toBe('"chris');
        expect(tags[1]).toBe('adam');
        expect(tags[2]).toBe('br"ian');
        expect(tags[3]).toBe('dave"');
    });

    it("parses tags with escaped quotes when delimiter switches to comma", function () {
        var tags = Tagulous.parseTags('""adam"" brian"", chris');
        expect(tags.length).toBe(2);
        expect(tags[0]).toBe('"adam" brian"');
        expect(tags[1]).toBe('chris');
    });

    it("parses tags ignoring empty tags", function () {
        var tags = Tagulous.parseTags('"adam" , , brian , ');
        expect(tags.length).toBe(2);
        expect(tags[0]).toBe('adam');
        expect(tags[1]).toBe('brian');
    });

    // Limit tests don't apply to javascript port
});


describe("Tagulous.parseTags spaceDelimiter=false", function () {
    var spaceDelimiter = false;
    it("parses tags with commas", function () {
        var tags = Tagulous.parseTags('adam,brian,chris', spaceDelimiter);
        expect(tags.length).toBe(3);
        expect(tags[0]).toBe('adam');
        expect(tags[1]).toBe('brian');
        expect(tags[2]).toBe('chris');
    });

    it("parses tags with spaces", function () {
        var tags = Tagulous.parseTags('adam brian chris', spaceDelimiter);
        expect(tags.length).toBe(1);
        expect(tags[0]).toBe('adam brian chris');
    });

    it("parses of tags with mix of commas and spaces", function () {
        var tags = Tagulous.parseTags('adam,brian chris', spaceDelimiter);
        expect(tags.length).toBe(2);
        expect(tags[0]).toBe('adam');
        expect(tags[1]).toBe('brian chris');
    });
});


describe("Tagulous.parseTags withRaw=true", function () {
    var spaceDelimiter = null,
        withRaw = true
    ;

    it("parses tags with commas", function () {
        var results = Tagulous.parseTags('chris,adam,brian', spaceDelimiter, withRaw),
            tags = results[0],
            raw = results[1]
        ;
        expect(tags.length).toBe(3);
        // Won't be sorted
        expect(tags[0]).toBe('chris');
        expect(tags[1]).toBe('adam');
        expect(tags[2]).toBe('brian');
        expect(raw.length).toBe(3);
        expect(raw[0]).toBe('adam,brian');
        expect(raw[1]).toBe('brian');
        expect(raw[2]).toBe(null);
    });
    it("parses tags with quotes which don't close", function () {
        var results = Tagulous.parseTags('"adam,one","brian,two","chris, dave', spaceDelimiter, withRaw),
            tags = results[0],
            raw = results[1]
        ;
        expect(tags.length).toBe(3);
        expect(tags[0]).toBe('adam,one');
        expect(tags[1]).toBe('brian,two');
        expect(tags[2]).toBe('"chris, dave');
        expect(raw.length).toBe(3);
        expect(raw[0]).toBe('"brian,two","chris, dave');
        expect(raw[1]).toBe('"chris, dave');
        expect(raw[2]).toBe(null);
    });

});


describe("Tagulous.renderTags", function () {
    it("renders tags", function () {
        var tagstr = Tagulous.renderTags(['adam', 'brian', 'chris']);
        expect(tagstr).toBe('adam, brian, chris');
    });

    it("renders tags and escapes quotes", function () {
        var tagstr = Tagulous.renderTags(['ad"am', '"brian', 'chris"', '"dave"']);
        expect(tagstr).toBe('""brian, ""dave"", ad""am, chris""');
    });

    it("renders tags and quotes commas and spaces", function () {
        var tagstr = Tagulous.renderTags(['adam brian', 'chris, dave', 'ed']);
        expect(tagstr).toBe('"adam brian", "chris, dave", ed');
    });

    it("parses simple rendered tags", function () {
        var tagstr = 'adam, brian, chris';
        var tags = Tagulous.parseTags(tagstr);
        var tagstr2 = Tagulous.renderTags(tags);
        expect(tags.length).toBe(3);
        expect(tags[0]).toBe('adam');
        expect(tags[1]).toBe('brian');
        expect(tags[2]).toBe('chris');
        expect(tagstr).toBe(tagstr2);
    });

    it("parses complex rendered tags", function () {
        var tagstr = '"""adam brian"", ""chris, dave", "ed, frank", gary';
        var tags = Tagulous.parseTags(tagstr);
        var tagstr2 = Tagulous.renderTags(tags);
        expect(tags.length).toBe(3);
        expect(tags[0]).toBe('"adam brian", "chris, dave');
        expect(tags[1]).toBe('ed, frank');
        expect(tags[2]).toBe('gary');
        expect(tagstr).toBe(tagstr2);
    });

});

