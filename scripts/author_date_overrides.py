"""Author editorial date overrides for the 164 undated historical-image records.

Each entry is the result of research: dates drawn from filename annotations,
yearbook/newspaper mastheads, postmarks, the San Gorgonio Pass Historical
Society timeline (httpssgphs.org/timeline.html), Beaumont institutional
histories (bank, churches, orchards), and direct visual analysis of the image
(automobiles, dress, architecture, gas-pump/postcard formats).

Writes data/editorial-overrides.json, then applies the ranges to
data/catalog.json, site/data/catalog.json and data/catalog.csv.
Originals are treated as read-only source; catalog.json is a generated artifact.
"""
import csv
import json
import shutil
from pathlib import Path

REPO = Path(r"C:\GitHub\san-gorgonio-historical-photo-catalog")

# id -> (start, end, display, confidence, basis)
# confidence: confirmed (explicit date/annotation), high (strong single anchor),
#             medium (reasoned era cues / subject anchor), low (broad range)
O = {
    # --- Mural-select records re-dated against Calisphere (2026-07-20) ---
    "img_650198dd9e4987ea": (1907, 1908, "1907", "high", "Calisphere CBEA_011 'Egan Ave, 1907-1908 Granite Building. J. Drew Frank Realty and Burt Carter's Livery Stable'; the mount is labeled 'Beaumont 1907'. Corrects the catalog's erroneous 'stagecoach, 1860'."),
    "img_6f833a14a7764e47": (1905, 1915, "c. 1905-1915", "low", "Same photo as Calisphere CBEA_134 'Southern Pacific Depot in Beaumont, looking east', which carries no date. The catalog's '1875' is untenable (Beaumont platted c.1887; the scene shows a large Edwardian crowd, a long passenger train and power/telegraph poles), so the year is widened on visual grounds."),
    "img_a4ddc941e94d3eed": (1909, 1909, "1909", "high", "Calisphere item c8kh0mpc 'Mellen Ranch, 1909'; the mount carries 'BEAUMONT ORCHARD 1909' and 'MELLEN RANCH 1909'. Corrects the catalog's 'Cherry Tree Farm, 1930' — it is the Mellen Ranch orchard, 1909."),

    # --- Beaumont High School yearbooks (year printed in filename) ---
    "img_5a70b41831a92160": (1946, 1946, "1946", "confirmed", "Year in filename; view of 6th St. from the 1946 Beaumont High School yearbook (SGPHS timeline confirms BHS yearbooks 1942-1950)."),
    "img_c228028c8fdfc647": (1949, 1949, "1949", "confirmed", "Year in filename; school band from the 1949 Beaumont High School yearbook."),
    "img_ada3474936428467": (1950, 1950, "1950", "confirmed", "Year in filename; majorettes from the 1950 Beaumont High School yearbook."),
    "img_7d31166d85dd49bd": (1950, 1950, "1950", "confirmed", "Year in filename; typing class from the 1950 Beaumont High School yearbook."),
    "img_4ac86175e34cb48f": (1938, 1948, "c. 1938-1948", "medium", "Real-photo postcard of the ~1930 Mission Revival high school (later Civic Center) with mature landscaping and paved street."),

    # --- Newspaper / letter mastheads (explicit dates) ---
    "img_9160017c82292a64": (1969, 1969, "March 21, 1969", "confirmed", "Record-Gazette masthead 3-21-69 in filename; new fire station under construction on Maple Ave (SGPHS timeline confirmed)."),
    "img_a48b18e93521487b": (1978, 1978, "Nov 28, 1978", "confirmed", "Record-Gazette masthead 11-28-78 in filename; council vote to contract fire services with CDF (SGPHS timeline confirmed)."),
    "img_06355ab9cdf953fb": (1968, 1968, "April 30, 1968", "confirmed", "Daily Record-Gazette masthead 4-30-68 in filename (SGPHS timeline confirmed)."),
    "img_530924ee0ded82c6": (1977, 1977, "May 26, 1977", "confirmed", "Letter dated 5-26-77 in filename."),

    # --- Bank of Beaumont ---
    "img_4b0acbe1458e33c0": (1909, 1909, "1909", "high", "Archival photo captioned 'Old Bank Building, Fifth and California' under construction; the first Bank of Beaumont was built in 1909."),
    "img_863f0fc9e94e4ebb": (2015, 2025, "c. 2015-2025 (1923 building)", "medium", "Contemporary color photo of the carved cornice 'Bank of Beaumont - Founded 1909 - Erected 1923'; the photo is recent, the building dates to 1923."),
    "img_e6fe5e33e99cc68f": (2018, 2025, "2020s", "high", "Filename 'today'; modern reference photo of the standing bank building."),
    "img_66a9280d1c1afbf9": (1923, 1940, "c. 1923-1940", "medium", "WCTU Fountain (dedicated 1910) beside the Bank of Beaumont at Fifth & Egan; that corner held the second bank, erected 1923, so the view postdates 1923."),
    "img_cd302d98752b29e0": (1923, 1940, "c. 1923-1940", "medium", "The second Bank of Beaumont (Fifth & Egan) was erected in 1923."),
    "img_e227a30890d191f3": (2010, 2025, "2010s-2020s", "low", "Generic digital-camera filename (IMG_3030); a modern photo tied to the first Bank of Beaumont site."),

    # --- Post office / early downtown / Fifth St / Egan Ave ---
    "img_9c26cfc39eca4fc9": (1910, 1915, "c. 1910-1915", "medium", "RPPC of the wooden Post Office; dirt street, horse wagon, Edwardian dress, and the WCTU fountain shelter (1910) present."),
    "img_5658eba56b079aef": (1885, 1895, "c. 1885-1895", "high", "SGPHS timeline's opening image 'Egan Avenue in its earliest days' - frontier strip, unpaved, no autos, dated c.1885-1895."),
    "img_157678621f95c278": (1898, 1908, "c. 1898-1908", "medium", "Dirt street with the Beaumont Land & Water Co. office and young eucalyptus saplings; no automobiles."),
    "img_7835865b7e46b59c": (1908, 1925, "c. 1908-1925", "low", "Vintage Egan Ave. postcard from a collector; 1910s-1920s commercial streetscape."),
    "img_92d81318b1127f4b": (1900, 1915, "c. 1900-1915", "low", "Egan Ave. 600 block (grouped with Summit House imagery, 1890s-1911)."),
    "img_676c1d159bb01165": (1887, 1895, "c. 1887 (original plat)", "medium", "George C. Egan surveyed and platted Beaumont's diagonal grid c.1887; the image is that town-plat map."),
    "img_82f263746528ece8": (1937, 1941, "c. late 1930s", "high", "Frasher's 'Street Scene, Beaumont' with the classical bank, Rexall Drugs and late-1930s automobiles."),
    "img_4239365a9df07707": (1918, 1924, "c. 1918-1924", "high", "RPPC with Model T touring cars, 'Gantt & Bro Groceries' and early-1920s dress."),
    "img_88e0efbd8026acce": (1929, 1933, "c. 1929-1933", "high", "Brick block with a Ford Model A coupe and 'Charles E. Crowther Real Estate'."),
    "img_e9f375f1600bc4d0": (2015, 2025, "2020s", "high", "Filename 'today'; modern reference photo of Fifth Street."),
    "img_37e600853baf16af": (1954, 1958, "c. 1955", "high", "Color snapshot of Pass City Grocery beside the bank, with a 1953 Chevrolet and 1955 Plymouth; shared to Facebook 2020."),
    "img_0880ba793548d705": (1908, 1925, "c. 1908-1925", "low", "Vintage Fifth Street postcard from the Steve Lech collection."),
    "img_9dee891466dac007": (1923, 1929, "c. mid-1920s", "medium", "S&S store corner with 1920s automobiles and a dirt street."),
    "img_03ae9abaca02013c": (1920, 1930, "c. 1920s", "low", "Interior of the S&S store; companion to the mid-1920s exterior view."),
    "img_0fe6d3036afcd3d6": (2015, 2025, "2020s", "high", "Filename 'today'; references I-10, modern reference photo."),

    # --- Railroad / depot / Estrada ---
    "img_934590dec97e3d15": (1909, 1918, "c. 1909-1918", "medium", "Postcard of the two-story (expanded) SP depot with steam locomotive and Edwardian-era figures; depot expansion ~1909."),
    "img_d5b3e8d2100926fd": (1908, 1918, "c. 1908-1918", "medium", "Rail-yard panorama with steam locomotive, water tower and lumber yard; no automobiles."),
    "img_eabd3578774e347f": (1908, 1918, "c. 1908-1918", "medium", "Multiple steam locomotives at the Beaumont roundhouse."),
    "img_07a9db15e22db499": (1905, 1915, "c. 1905-1915", "medium", "Foreground locomotive is SP No. 2789 (C-9 Harriman Common Standard 2-8-0, Baldwin ~1905), read off the smokebox plate, headlight number board and shoulder marking; the class was built from ~1905, the high-mounted oil headlight predates SP's 1910s electric conversions, and Calisphere dates the scene to the early 1900s. Supersedes the SGPHS timeline's '1890s' reading."),
    "img_3b097e0808432587": (1915, 1940, "c. 1915-1940", "low", "SP section workforce; SGPHS notes women documented sweeping the tracks in the early-rail/Estrada era."),
    "img_0ab722136d7bd1be": (1940, 1949, "c. 1940s", "medium", "SGPHS timeline dates the Estrada family at meals inside the SP section house to the 1940s."),
    "img_ca02842503e130c9": (1940, 1949, "c. 1940s", "medium", "SGPHS timeline dates the Estrada family in their SP section house to the 1940s."),
    "img_a7a6b112d9c297dd": (1915, 1930, "c. 1915-1930", "low", "Youthful portrait of Luis Estrada, who worked for the SP for decades."),
    "img_4ec3e978a2772b6b": (1910, 1935, "c. 1910-1935", "low", "SP railroad-worker group portrait at the Beaumont depot including Luis Estrada."),
    "img_4a9ee3f3baeb6a26": (1910, 1935, "c. 1910-1935", "low", "SP railroad-worker group portrait including Luis Estrada."),
    "img_6ddebbe0de2a589d": (2018, 2021, "c. 2018-2021", "medium", "Photo of the Luis Estrada Road street sign; the road's 20th anniversary was marked in 2021."),
    "img_c822a8c6bb7c2f67": (2018, 2021, "c. 2018-2021", "medium", "Photo of the Luis Estrada Road street sign (modern)."),
    "img_3c18a28de48c53d4": (2018, 2021, "c. 2018-2021", "medium", "Photo of the Luis Estrada Road street sign with stop sign (modern)."),
    "img_48e0a1029b9b35cf": (2010, 2024, "2010s-2020s", "low", "Family snapshot of the California State Railroad Museum's life-size figure of Luis Estrada, which the museum created in 2005 (CSRM finding aid MS 871); exact visit date unknown."),
    "img_39722a07ed88a499": (2010, 2024, "2010s-2020s", "low", "Family snapshot of the California State Railroad Museum's life-size figure of Luis Estrada, which the museum created in 2005 (CSRM finding aid MS 871); exact visit date unknown."),
    "img_9acdf5b823073389": (2010, 2024, "2010s-2020s", "low", "Family snapshot of the California State Railroad Museum's life-size figure of Luis Estrada, which the museum created in 2005 (CSRM finding aid MS 871); exact visit date unknown."),
    "img_99913db9881316f3": (2005, 2005, "2005", "high", "Close-up of the California State Railroad Museum's life-size figure of Luis Estrada, created 2005 (CSRM finding aid MS 871); the scanned page is dated 2/23/2005."),

    # --- Hotel Beaumont ---
    "img_70f5802804fd1652": (1900, 1908, "c. 1900-1908", "medium", "Elevated townscape with the pre-1909 single-story depot, Peter Allen Store, and the Hotel Beaumont on the hill (burned 1909)."),
    "img_049b709d6ffb773a": (1890, 1909, "c. 1890-1909", "medium", "Vista including the Hotel Beaumont, which stood from 1888 until it burned in August 1909."),
    "img_c6fa941a29b0f0cd": (1900, 1909, "c. 1900-1909", "medium", "The Hotel Beaumont was renamed Hotel Edinburgh shortly before it burned in 1909."),
    "img_6345c804830d0a07": (2025, 2025, "May 2025", "confirmed", "Filename dated 5-8-25; Google reference image of the site today."),
    "img_c01f0729b7635aa7": (2025, 2025, "May 2025", "confirmed", "Filename dated 5-8-25; Google reference image of the site today."),

    # --- Land & Water Co / orchards / ranch water ---
    "img_b2764c9151e44824": (1890, 1905, "c. 1890-1905", "medium", "Beaumont Land & Water Co. was the founding-era developer, active late 1880s into the 1900s."),
    "img_6278e20aa65dd6a8": (1895, 1910, "c. 1895-1910", "medium", "Beaumont Land & Water Co. pumping station; Edgar Canyon well drilling documented 1908."),
    "img_83b4208d7a588795": (1900, 1912, "c. 1900-1912", "medium", "Beaumont water well; Edgar Canyon well drilling documented 1908."),
    "img_9a09c6788b0dddf1": (1895, 1915, "c. 1895-1915", "low", "Early ranch scene at the Bliss Ranch well."),
    "img_3e252c3b2ce712aa": (1900, 1925, "c. 1900-1925", "low", "Early Beaumont apple/cherry orchards; the orchard economy defined the town ~1900-1920s."),

    # --- Churches ---
    "img_5430b97f619e1088": (2010, 2025, "2010s-2020s (1934 building)", "medium", "Modern photo of the stone Presbyterian 'rock church', built 1934, with current signage."),
    "img_da743e866c6368cc": (2010, 2025, "2010s-2020s (1934 building)", "high", "Modern color photo of the stone Presbyterian rock church (built 1934) with current signage."),
    "img_b4e6ea6952262482": (2010, 2025, "2010s-2020s (1934 building)", "medium", "Modern photo of the 1934 stone Presbyterian church."),
    "img_1ace86d145209734": (1934, 2025, "1934 or later (1934 church interior)", "low", "Interior of the Presbyterian rock church, completed 1934; capture date uncertain."),
    "img_3d84769134889400": (2010, 2025, "2010s-2020s", "low", "Close-up of the church's rock construction; modern documentation of the 1934 building."),
    "img_a144edcec7a50be8": (1930, 1940, "c. 1930-1940", "medium", "SGPHS timeline dates First Christian Church at 701 Egan Ave. to 1930-1940; image shows it under construction."),
    "img_1d5ad1237f7755e2": (1925, 1945, "c. 1925-1945", "medium", "Faded photo of the small adobe barrio chapel with dirt yard, predating the larger stucco church; received June 2025."),
    "img_add874f3a7967842": (1956, 1963, "c. late 1950s", "high", "Color slide of a First Communion outside Sacred Heart barrio church, with ~1953-54 cars and a 1956-62 yellow California plate."),
    "img_22f62627c5d79f7e": (1930, 1960, "c. 1930-1960", "low", "Sacred Heart barrio parish, Beaumont; specific date not recorded."),

    # --- Fire department / city hall ---
    "img_7a0159037504313e": (1955, 1965, "c. late 1950s-early 1960s", "medium", "SGPHS timeline places the volunteer fire department at 500 Grace Ave. in the late 1950s-early 1960s."),
    "img_f03f7f375191edf6": (1973, 1980, "c. 1975", "medium", "Antique hand hose-cart displayed at a 1960s breeze-block fire station, with a mid-1970s GMC engine in the bay."),
    "img_1ac667107bd74996": (1960, 1978, "c. 1960s-1970s", "low", "Beaumont Fire Department work and dress uniforms; the department modernized through the 1960s-70s."),
    "img_04328f685390128c": (2000, 2020, "c. 2000s-2010s", "low", "Photo of a memorial to volunteer firefighter Scott Karnitz; a modern commemorative image."),
    "img_8a20e0efb687510c": (2000, 2020, "c. 2000s-2010s", "low", "Photo of a memorial to volunteer firefighter Scott Karnitz; a modern commemorative image."),
    "img_67d561c6f67c1ba2": (1995, 2020, "c. late 20th-early 21st c.", "low", "Newspaper clipping about volunteer firefighter Scott Karnitz."),
    "img_a9b8f17ec8b1a61d": (1935, 1955, "c. 1935-1955", "low", "Historical photo of the combined City Hall / Fire / Police at 500 Grace Ave.; received Jan 2023."),
    "img_03056ebb373ddd81": (1935, 1955, "c. 1935-1955", "low", "Old City Hall at 500 Grace Ave.; mid-century."),

    # --- Dowling family & orchard store ---
    "img_ed9a0626308ebccf": (1918, 1925, "c. 1918-1925", "medium", "Young Francis Dowling Sr. beside a Model T-based 'Golden State Cherry Orchard' truck with wooden-spoke wheels."),
    "img_9299c7a090b03878": (1915, 1925, "c. 1915-1925", "low", "Youthful portrait of Francis Dowling Sr."),
    "img_6205c940ef544e0b": (1900, 1920, "c. 1900-1920", "low", "Couple portrait of the elder Dowling generation (Francis Marion Sr. and Iola Stower Dowling)."),
    "img_953fbfaa8e42a2fb": (1900, 1918, "c. 1900-1918", "low", "Youthful portrait of Iola Stower Dowling."),
    "img_57a9c9df6e55e692": (1930, 1945, "c. 1930-1945", "low", "Two-generation Dowling portrait (Sr. with grown Jr.)."),
    "img_fe6493dfb389b7f5": (1930, 1945, "c. 1930-1945", "low", "Francis Dowling Jr. and Estella; adult portrait."),
    "img_36bc04455099c9d7": (1945, 1958, "c. 1945-1958", "low", "Francis Dowling Jr. with his son John sorting cherries; mid-century orchard work."),
    "img_a6ec55f14a4d13dc": (1945, 1960, "c. 1945-1960", "low", "Francis Dowling Jr. with an orchard clamp truck."),
    "img_1ad76840ab48ba0e": (1950, 1968, "c. 1950s-1960s", "low", "Portrait of John Dowling (Francis Jr.'s son)."),
    "img_dc9b98dd0bb1264f": (1952, 1965, "c. 1950s-1960s", "medium", "Dowling Fruit Orchard roadside stand; the store opened in 1952."),
    "img_2eee4fa95a275d4d": (1952, 1968, "c. 1950s-1960s", "medium", "Dowling Fruit Orchard stand signage; the store opened in 1952."),
    "img_72b5acdf8b88fc6c": (1952, 1968, "c. 1950s-1960s", "medium", "Interior of the Dowling Fruit Orchard store (opened 1952)."),
    "img_eebd80e2b2180cca": (1952, 1968, "c. 1950s-1960s", "medium", "Dowling store produce display (store opened 1952)."),
    "img_4eeb78c48b2bca4b": (2015, 2025, "2010s-2020s", "high", "Filename 'contemporary'; modern photo of the Dowling store."),

    # --- Eyer / Smoot family portraits ---
    "img_291537b3068812cf": (1890, 1915, "c. 1890-1915", "low", "Portrait of an Eyer-family member (early Beaumont settlers; Eyer House c.1915-1920)."),
    "img_dbf7e0bb619c1c74": (1890, 1915, "c. 1890-1915", "low", "Eyer-family portrait (Cora K. Eyer)."),
    "img_2fa19df607bf43e1": (1915, 1920, "c. 1915-1920", "confirmed", "Date written in filename ('circa 1915-1920')."),
    "img_4e6f8597cedbda5b": (1885, 1920, "c. 1885-1920 (subject 1859-1935)", "low", "Portrait of Jane Eyer Smoot; filename gives her life dates 1859-1935."),
    "img_a7581c3a3616e8da": (1885, 1920, "c. 1885-1920 (subject 1859-1935)", "low", "Portrait of Jane Eyer Smoot (1859-1935)."),
    "img_317c261e7e95cb9d": (1885, 1915, "c. 1885-1915", "low", "Couple portrait; filename gives Kenneth Russell Smoot's dates 1857-1932."),

    # --- Stewart family & ranch ---
    "img_e6c2b250138da121": (1908, 1913, "c. 1908-1913", "high", "Stewart family at the ranch barn; women in Edwardian long skirts and oversized 'Merry Widow' hats (c.1908-12)."),
    "img_68556e4afecfa748": (1908, 1918, "c. 1908-1918", "medium", "Portrait of the Stewart sisters; Laura May was photographed 1911 and crowned first Cherry Queen 1919."),
    "img_4a82e2c89eb4a27d": (1910, 1920, "c. 1910-1920", "medium", "Reznor on horseback and Laura May 'at the wheel' of an early automobile; Laura May's 1911 era."),
    "img_7b302ec1a5a6c157": (1900, 1915, "c. 1900-1915", "low", "Portrait of Reznor Stewart (father of Laura May Stewart)."),
    "img_e223c8fe27b85e0d": (1900, 1915, "c. 1900-1915", "low", "Portrait of Reznor Stewart; filename notes date unknown."),
    "img_1dfdd8cac1f62558": (1900, 1915, "c. 1900-1915", "low", "Portrait of Reznor Stewart; filename notes date unknown."),
    "img_df9bd9231a83651c": (1900, 1915, "c. 1900-1915", "low", "Portrait of Reznor Stewart; filename notes date unknown."),
    "img_2846f7be40e9aff6": (1900, 1930, "c. 1900-1930", "low", "Farm equipment at the Stewart Ranch."),
    "img_cfdaf786f32d7ba0": (1900, 1930, "c. 1900-1930", "low", "Farm equipment at the Stewart Ranch."),
    "img_b3dcb09d831e2058": (1945, 1965, "c. 1945-1965", "low", "Laura May Stewart as an older woman in her family-history collection room."),
    "img_64fee8a381ae5df5": (2020, 2020, "May 2020", "confirmed", "Filename dated 5-15-20; Google image of Stewart Sunnyslope Cemetery."),

    # --- Guy Bogart ---
    "img_a85c852bf4ca3f39": (1935, 1948, "c. 1935-1948", "medium", "Elderly Guy Bogart at his desk with an 'Easter Sunrise / Bogart Bowl' poster."),
    "img_b0d82053666b74fe": (1935, 1948, "c. 1935-1948", "medium", "Guy Bogart in his home office; companion to the desk portrait."),
    "img_da155fda02d882ee": (1925, 1945, "c. 1925-1945", "low", "Guy Bogart handing out apples at a community event."),
    "img_0092d056a315fe98": (2020, 2020, "Feb 2020", "confirmed", "Filename dated 2-8-20; modern photo of the Bogart House."),
    "img_c8be9dda2808f47c": (1915, 1940, "c. 1915-1940", "low", "Historical photo of Guy Bogart's house from the Library District archive."),

    # --- Roadside businesses (visual dating) ---
    "img_ef0e1fe665c580a0": (1938, 1946, "c. 1940", "high", "Frasher's postcard 'Beaumont on U.S. Highways 60 and 99' showing Sam's Cafe with late-1930s/early-1940s automobiles."),
    "img_21f5dda0d6f26b4a": (1941, 1946, "c. early-mid 1940s", "high", "Photo of Sam's Cafe corner with a 1941-42 Chevrolet pickup and men in 1940s fedoras."),
    "img_484acf24f5126598": (1946, 1950, "c. late 1940s", "high", "Highway view (Desert Outpost Cafe) with a late-1940s fastback sedan and cabins/dancing signage."),
    "img_92af244203629094": (1947, 1953, "c. late 1940s-early 1950s", "high", "Frasher's postcard of the El Rancho Motel with postwar 1940s automobiles and cocktail signage."),
    "img_2d0928cd5901f761": (1945, 1955, "c. late 1940s-1950s", "medium", "Colorized linen postcard of the Streamline Moderne Fireside Inn."),
    "img_6feb4c505e0a58be": (1960, 1978, "c. 1960s-1970s", "medium", "Matchbook for Joe's Cafe (1232 E. 6th St.) with an all-numeric 7-digit phone number, indicating the 1960s-70s."),
    "img_e91452d502f8cc96": (1951, 1955, "c. early-mid 1950s", "high", "RPPC of Sixth Street with early-1950s automobiles, 'George's 5&10' and 'Bob's Cafe'."),
    "img_228a900cb9c1637b": (1945, 1946, "c. 1945", "high", "Frasher's postcard of Sixth Street with a Greyhound bus, ~1940 cars, and the Beaumont Theatre showing 'Masquerade in Mexico' (1945)."),
    "img_a83e9024f8e65c3f": (1955, 1958, "c. mid-late 1950s", "high", "Color chrome postcard of Sixth Street with mid-1950s automobiles and a roller-rink sign."),
    "img_e3de81c2cb7655c8": (1925, 1932, "c. mid-late 1920s", "high", "RPPC of the Spanish Revival Triangle Service Station with 1920s visible-register pumps and a Model T-era car."),
    "img_8241a89edda429c5": (1937, 1942, "c. late 1930s", "high", "Frasher's postcard showing the former Triangle station repurposed as Chamber of Commerce/Logan's, with a late-1930s sedan."),
    "img_fd15a86cd86982d6": (1922, 1930, "c. 1920s", "high", "RPPC of the Triangle Service Station with flat-capped attendants and 1920s visible-register gas pumps."),
    "img_1c61ef08adc421b9": (2018, 2025, "2020s", "high", "Filename 'today'; modern reference photo of the Triangle Gas Station site."),

    # --- Ramona's / Torres / Vargas ---
    "img_2ffb4cd6b691c887": (1958, 1970, "c. 1960s", "medium", "Ramona and Frank Torres at a banquet; early-1960s bouffant styling."),
    "img_f3ff85c652f90c21": (1958, 1970, "c. 1960s", "low", "Ramona and Frank Torres portrait; 1960s."),
    "img_ba7b9a02b3a0292c": (1958, 1970, "c. 1960s", "low", "Ramona and Frank Torres portrait; 1960s."),
    "img_6b0ff0ed19b0fb9e": (1955, 1975, "c. 1955-1975", "low", "Portrait of Ramona Torres, namesake of Ramona's Mexican Cafe."),
    "img_dec634939b47e13c": (2018, 2025, "2020s", "high", "Modern smartphone snapshot of the elderly Vargas couple at a birthday in a contemporary home."),
    "img_1098cac0279a0fdd": (2018, 2025, "2020s", "high", "Modern photo of Christine and Gil Vargas Sr."),
    "img_4b3616cbe2898cea": (2018, 2025, "2020s", "high", "Modern photo of Christine and Gil Vargas Sr."),
    "img_21b5c2878b287c35": (2025, 2025, "May 31, 2025", "confirmed", "Filename dated 5-31-25; Cherry Festival parade."),
    "img_5bcc7a2a42f3de62": (2025, 2025, "May 31, 2025", "confirmed", "Filename dated 5-31-25; Cherry Festival parade."),
    "img_cb8fe08683e0e832": (2025, 2025, "May 31, 2025", "confirmed", "Filename dated 5-31-25; Cherry Festival parade."),
    "img_3f4c4ca617098fd8": (2018, 2025, "2020s", "medium", "Modern photo of the current Ramona's Mexican Cafe building."),
    "img_d36ca3005fd7406a": (2018, 2025, "2020s", "medium", "Modern photo of the current Ramona's Mexican Cafe building."),
    "img_8ee30e567a4b5e66": (2018, 2025, "2020s", "medium", "Modern photo of the current Ramona's Mexican Cafe (brick facade)."),
    "img_a04b2576fd8d515e": (2018, 2025, "2020s", "medium", "Modern photo of the current Ramona's Mexican Cafe building."),
    "img_87313621a59a7991": (2018, 2025, "2020s", "medium", "Modern photo of the current Ramona's Mexican Cafe building."),
    "img_040513e8698b345f": (2018, 2025, "2020s", "medium", "Modern photo of the current Ramona's Mexican Cafe building."),
    "img_11892e76e7df49d3": (2018, 2025, "2020s", "medium", "Modern photo of the current Ramona's Mexican Cafe building."),
    "img_8da5c565955aa314": (2018, 2025, "2020s", "medium", "Modern photo of the current Ramona's Mexican Cafe building."),
    "img_99255ef1fe8299f3": (2018, 2025, "2020s", "medium", "Modern photo of the current Ramona's Mexican Cafe building."),
    "img_9ae52f4064af37bc": (2018, 2025, "2020s", "medium", "Modern photo of the current Ramona's Mexican Cafe building."),
    "img_00cfeb70e204b1b8": (2018, 2025, "2020s", "medium", "Modern photo of the current Ramona's Mexican Cafe (sombrero bushes)."),

    # --- WCTU fountain / Triangle Park ---
    "img_591fdce9e557db2e": (2018, 2025, "2020s", "high", "Modern photo of the surviving WCTU stone fountain in Triangle Park (with a 2014+ SUV)."),
    "img_284993317d64a5e4": (2018, 2025, "2020s", "high", "Modern photo of the WCTU stone fountain in Triangle Park."),
    "img_8aa40ef6d2dbc201": (2018, 2025, "2020s", "high", "Modern photo of the WCTU stone fountain in Triangle Park."),
    "img_40d6c2b8e19fd527": (2018, 2025, "2020s", "high", "Modern photo of the WCTU stone fountain in Triangle Park."),
    "img_a999fd2c808b66bb": (2018, 2025, "2020s", "high", "Modern photo of the WCTU stone fountain in Triangle Park."),
    "img_3c8f15b64eec6c9e": (2018, 2025, "2020s", "high", "Modern photo of the WCTU stone fountain in Triangle Park."),
    "img_7d409eb4d324e61e": (1923, 1940, "c. 1923-1940", "medium", "WCTU Fountain (1910) at its original Fifth & Egan location beside the Bank of Beaumont (that corner's bank erected 1923); later moved to Triangle Park."),
    "img_7dbe92a607028a11": (2022, 2022, "March 2022", "confirmed", "Filename dated 3-16-22; Google photo of Triangle Park."),

    # --- Gateway Gazette ---
    "img_f711da54b73a8423": (1908, 1912, "c. 1908-1912", "high", "Blue-duotone advertising postcard 'The Office of the Gateway Gazette as it now appears'; the paper published from ~1908 (an issue dated April 30, 1908 is documented)."),
    "img_19665af80792888c": (1908, 1912, "c. 1908-1912", "medium", "Gateway Gazette interior advertising postcard, contemporary with the paper's ~1908 era."),

    # --- Trees / deodars ---
    "img_e0a4861e5d654fdb": (1908, 1915, "c. 1908-1915", "medium", "Hand-colored divided-back postcard of mature eucalyptus (planted ~1900) with a Craftsman bungalow."),
    "img_67656824cbb42ffc": (1940, 1965, "c. 1940s-1960s", "medium", "Deodar cedars on Beaumont Ave. were planted in 1930; a color postcard of the mature trees dates to roughly the 1940s-1960s."),
    "img_8ecf8879b0fffd2d": (1935, 1960, "c. 1935-1960", "medium", "Deodars planted 1930; vintage postcard of the maturing tree-lined avenue."),
    "img_38d2d7286d1a066a": (2018, 2025, "2020s", "high", "Filename 'today'; modern photo of the deodar avenue."),

    # --- Schools / civic buildings ---
    "img_31bfa277fbd3230d": (1890, 1905, "c. 1890s", "medium", "Frame schoolhouse with bell cupola and a horse buggy; the first Wellwood School (1890-93 era)."),
    "img_35a3c2b0b73a7892": (1962, 1975, "c. 1960s-1970s", "medium", "Architect's watercolor rendering (Harry T. Macdonald & Assoc.) of a mid-century-modern school."),
    "img_477fd73b5434521f": (1890, 1910, "c. 1890-1910", "medium", "The McCoy lumberyard supplied building materials to Beaumont in the late 19th and early 20th centuries."),
    "img_37bbc779f837532c": (2015, 2024, "c. 2015-2024", "medium", "Contemporary Historical Society house-tour photo (McCoy House) credited to Pat Murkland."),
    "img_816fb6e3233bbf73": (2025, 2025, "April 2025 (historic hotel)", "confirmed", "Filename dated 4-28-25; modern photo of the Sunset Plaza Hotel building (the hotel dates to c.1948)."),

    # --- Portraits / misc ---
    "img_c39e3df610ea24d9": (1845, 1867, "c. 1850s-1860s (Pauline Weaver, d.1867)", "medium", "Engraved portrait of frontiersman Pauline Weaver (1797-1867); an illustration, not a dated photograph, depicting his mid-19th-century era."),
    "img_e5e3407036c3c2c5": (2010, 2010, "April 2010", "confirmed", "Scrapbook page annotated 'April 2010'; color aerial of built-out Beaumont with I-10."),
}


def decade_of(start):
    return (start // 10) * 10 if start is not None else None


def main():
    catalog_path = REPO / "data" / "catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    ids_in_catalog = {r["id"] for r in catalog["records"]}

    # Coverage check: every override id must exist; report undated not covered.
    undated = {r["id"] for r in catalog["records"]
               if r["date"]["display"] == "Undated" and not (r["date"].get("start") or r["date"].get("end"))}
    missing = undated - set(O)
    unknown = set(O) - ids_in_catalog
    assert not unknown, f"Override ids not in catalog: {unknown}"
    print(f"Undated records: {len(undated)}  |  Overrides authored: {len(O)}  |  Uncovered: {len(missing)}")
    if missing:
        for r in catalog["records"]:
            if r["id"] in missing:
                print("  UNCOVERED:", r["id"], "-", r["title"])
        raise SystemExit("Refusing to write: some undated records lack an override.")

    # Write the editorial-overrides layer.
    overrides_doc = {
        "schema_version": "1.0.0",
        "description": "Researched date ranges for records the pipeline left undated. "
                       "Sources: filename annotations, yearbook/newspaper mastheads, postmarks, "
                       "the San Gorgonio Pass Historical Society timeline, Beaumont institutional "
                       "histories, and visual analysis (vehicles, dress, architecture, postcard format).",
        "confidence_levels": {
            "confirmed": "explicit date in the image, filename, masthead, postmark, or a source annotation",
            "high": "strong single anchor (dated postcard series, documented construction year, decisive visual cue)",
            "medium": "reasoned from era cues or a subject's known active period",
            "low": "broad but defensible range; further confirmation welcome",
        },
        "overrides": {
            rid: {"date_start": s, "date_end": e, "display": disp,
                  "confidence": conf, "basis": basis}
            for rid, (s, e, disp, conf, basis) in O.items()
        },
    }
    (REPO / "data" / "editorial-overrides.json").write_text(
        json.dumps(overrides_doc, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Wrote data/editorial-overrides.json")

    # Apply to catalog.json and site/data/catalog.json.
    def apply(records):
        n = 0
        for r in records:
            ov = O.get(r["id"])
            if not ov:
                continue
            s, e, disp, conf, basis = ov
            r["date"] = {
                "start": s, "end": e, "display": disp, "confidence": conf,
                "editable": True, "source": "editorial_research", "basis": basis,
            }
            r["decade"] = decade_of(s)
            if r.get("research_status") == "Needs research":
                r["research_status"] = "Date researched"
            n += 1
        return n

    for p in (REPO / "data" / "catalog.json", REPO / "site" / "data" / "catalog.json"):
        doc = json.loads(p.read_text(encoding="utf-8"))
        # Re-sort so newly dated records fall into chronological order like the pipeline does.
        n = apply(doc["records"])
        doc["records"].sort(key=lambda it: (it["date"]["start"] is None,
                                            it["date"]["start"] or 9999,
                                            it["title"].lower()))
        p.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Applied {n} overrides -> {p.relative_to(REPO)}")

    # Refresh data/catalog.csv date columns from the updated catalog.
    cat = json.loads((REPO / "data" / "catalog.json").read_text(encoding="utf-8"))
    csv_path = REPO / "data" / "catalog.csv"
    if csv_path.exists():
        by_id = {r["id"]: r for r in cat["records"]}
        rows = []
        with csv_path.open("r", newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            fields = reader.fieldnames
            for row in reader:
                r = by_id.get(row["id"])
                if r:
                    if "date_start" in row:
                        row["date_start"] = r["date"]["start"]
                    if "date_end" in row:
                        row["date_end"] = r["date"]["end"]
                    if "decade" in row:
                        row["decade"] = r["decade"]
                    if "research_status" in row:
                        row["research_status"] = r.get("research_status", row.get("research_status"))
                rows.append(row)
        with csv_path.open("w", newline="", encoding="utf-8-sig") as fh:
            writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        print("Refreshed data/catalog.csv date columns")


if __name__ == "__main__":
    main()
