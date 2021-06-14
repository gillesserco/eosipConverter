
from cStringIO import StringIO

# This table lists information about ERS-1 cycles
#
# Each record lists the information for one repeat cycle:
# - Mission phase
# - Cycle number
# - First internal pass number
# - Last internal pass number
# - Start time in UTC YYMMDDHHMMSS.sss (with sss fraction of seconds)
# - Stop time in UTC YYMMDDHHMMSS.sss (with sss fraction of seconds)
# - Number of tracks available
# - Number of records for this cycle
#
HEADER="ph cyc pass0 pass1 starttime        endtime          #trx  #recs"

DATA="a 000 0530 1002 950429093900.086 950515215935.555  348  628364,\
a 001 0001 1002 950515220934.416 950619215931.364  950 1686713,\
a 002 0001 1002 950619220938.445 950724215924.197  978 1671609,\
a 003 0001 1002 950724220946.627 950828215918.796  945 1632497,\
a 004 0001 1002 950828220944.246 951002215934.245  895 1633446,\
a 005 0001 1002 951002220941.319 951106215920.212  976 1713122,\
a 006 0001 1002 951106220943.386 951211215917.570  960 1674204,\
a 007 0001 1002 951211220944.549 960115215924.801  939 1663203,\
a 008 0001 1002 960115220940.959 960219215928.871  919 1650992,\
a 009 0001 1002 960219220943.263 960325215919.541  954 1722335,\
a 010 0001 1002 960325220935.713 960429215928.409  977 1760774,\
a 011 0001 1002 960429220943.729 960603215915.759  927 1638306,\
a 012 0001 1002 960603220940.844 960708215928.246  959 1655084,\
a 013 0001 1002 960708220942.797 960812215914.820  997 1708842,\
a 014 0001 1002 960812220939.439 960916215917.414  960 1670447,\
a 015 0001 1002 960916220944.182 961021215913.148  991 1763634,\
a 016 0001 1002 961021220941.444 961125215921.421  972 1709568,\
a 017 0001 1002 961125220936.234 961230215904.094  935 1657083,\
a 018 0001 1002 961230220939.692 970203215920.188  991 1786835,\
a 019 0001 1002 970203220936.820 970310215921.924  940 1719157,\
a 020 0001 1002 970310220940.533 970414215853.239  955 1730872,\
a 021 0001 1002 970414220940.830 970519215917.913  952 1701618,\
a 022 0001 1002 970519220938.561 970623215924.454  967 1679321,\
a 023 0001 1002 970623220954.931 970728215923.143  971 1656413,\
a 024 0001 1002 970728220938.814 970901215922.940 1000 1739820,\
a 025 0001 1002 970901220938.368 971006215921.557  997 1773046,\
a 026 0001 1002 971006220937.590 971110215912.153 1000 1762443,\
a 027 0001 1002 971110220934.151 971215215917.822  999 1765401,\
a 028 0001 1002 971215220934.148 980119215906.401  992 1774946,\
a 029 0001 1002 980119220933.951 980223215909.338  992 1796095,\
a 030 0001 1002 980223220930.575 980330215920.270  985 1775291,\
a 031 0001 1002 980330220934.853 980504215918.601 1000 1802706,\
a 032 0001 1002 980504220957.860 980608215916.622  916 1619887,\
a 033 0001 1002 980608220933.968 980713215905.753  984 1686063,\
a 034 0001 1002 980713220930.603 980817215910.610  996 1711933,\
a 035 0001 1001 980817220934.701 980921211355.285  975 1706535,\
a 036 0001 1002 980921220935.184 981026215907.280  982 1730389,\
a 037 0001 1002 981026220931.902 981130215906.033  964 1695828,\
a 038 0001 1002 981130220929.705 990104215858.222 1001 1785961,\
a 039 0001 1002 990104220928.208 990208215916.741  997 1813141,\
a 040 0001 1002 990208220931.502 990315215917.710  998 1820615,\
a 041 0001 1002 990315220939.174 990419215913.280 1000 1825564,\
a 042 0001 1002 990419220945.128 990524215910.122  970 1724489,\
a 043 0001 1002 990524220937.385 990628215907.781  983 1711791,\
a 044 0001 1002 990628221006.556 990802215905.630  991 1694923,\
a 045 0001 1002 990802220942.565 990906215901.422 1000 1755765,\
a 046 0001 1002 990906220931.420 991011215905.574  999 1769924,\
a 047 0001 1002 991011220932.559 991115215907.419  984 1731399,\
a 048 0001 1002 991115220932.979 991220215911.817  975 1726533,\
a 049 0001 1002 991220220933.470 000124215916.958  936 1694286,\
a 050 0001 1002 000124220934.299 000228215919.559  907 1644700,\
a 051 0001 1002 000228220939.774 000403211420.151  980 1787220,\
a 052 0001 1002 000403220957.255 000508215917.793 1002 1799767,\
a 053 0001 1002 000508220943.121 000612215859.415 1002 1777764,\
a 054 0001 1002 000612220936.090 000717215914.701  640 1095601,\
a 055 0001 1002 000717220942.459 000821215919.002 1002 1737821,\
a 056 0001 1002 000821220947.390 000925215922.685 1002 1769985,\
a 057 0001 1002 000925220948.586 001030215918.862  915 1630152,\
a 058 0001 1002 001030220944.565 001204215919.017 1002 1776070,\
a 059 0001 1002 001204220953.758 010108215925.166  975 1743277,\
a 060 0001 1002 010108220954.743 010212215920.083  343  613135,\
a 061 0001 1002 010212225350.431 010319215931.097 1001 1760366,\
a 062 0001 1002 010319225410.792 010423215917.885  988 1750894,\
a 063 0001 1002 010423220937.325 010528215853.736  922 1644471,\
a 064 0001 1002 010528220927.471 010702215834.632  996 1734722,\
a 065 0001 1002 010702225319.935 010806215833.322 1002 1729690,\
a 066 0001 1002 010806220852.200 010910215803.549  990 1729371,\
a 067 0001 1002 010910220828.756 011015215743.784  985 1752356,\
a 068 0001 1002 011015220811.913 011119215720.115  936 1658226,\
a 069 0001 1002 011119220747.999 011224215732.432  969 1723222,\
a 070 0001 1002 011224220752.510 020128215724.787 1001 1809361,\
a 071 0001 1002 020128225208.711 020304215729.078  982 1763748,\
a 072 0001 1002 020304220754.988 020408215733.661  633 1150743,\
a 073 0001 1002 020408220756.642 020513215742.066  969 1745619,\
a 074 0001 1002 020513220812.646 020617215749.112  997 1750046,\
a 075 0001 1002 020617220810.826 020722215743.402  993 1705013,\
a 076 0001 1002 020722220815.232 020826215741.800 1002 1745990,\
a 077 0001 1002 020826220806.548 020930215739.784 1002 1786864,\
a 078 0001 1002 020930220808.800 021104215731.437  977 1724203,\
a 079 0001 1002 021104220802.654 021209211240.737  974 1727677,\
a 080 0011 1002 021210063010.153 030113215747.026  980 1742697,\
a 081 0001 1002 030113220804.627 030217215743.239  997 1801977,\
a 082 0001 1002 030217220800.744 030324215733.800  994 1800197,\
a 083 0001 1001 030324220755.452 030428211220.157  999 1809336,\
a 084 0001 1002 030428220802.398 030602215739.969  893 1575213,\
a 085 0001 0842 030602220823.256 030702070914.719  563  952438,\
a 086 0247 1002 030716130632.526 030811211301.828  527  109213,\
a 087 0001 1002 030811224321.555 030915212258.758  704  194223,\
a 088 0001 1002 030915222921.671 031020211407.365  759  284038,\
a 089 0001 1002 031020222928.229 031124211409.210  737  263543,\
a 090 0001 1002 031124222910.384 031229211409.045  741  260633,\
a 091 0001 1002 031229224310.208 040202212253.588  760  258069,\
a 092 0001 1002 040202222917.026 040308212251.450  801  271485,\
a 093 0001 1002 040308222915.254 040412212253.225  809  273841,\
a 094 0001 1002 040412222915.193 040517212258.075  792  270291,\
a 095 0001 1002 040517222922.921 040621212300.643  795  267282,\
a 096 0001 1002 040621222924.516 040726212305.714  779  262418,\
a 097 0001 1002 040726222925.448 040830212310.683  720  274329,\
a 098 0001 1002 040830222931.305 041004212256.293  831  303699,\
a 099 0001 1002 041004222925.597 041108212257.485  826  290971,\
a 100 0001 1002 041108222918.532 041213212258.250  858  288635,\
a 101 0001 1002 041213222924.198 050117212202.078  779  264378,\
a 102 0001 1002 050117222921.704 050221212253.422  845  287475,\
a 103 0001 1002 050221222915.261 050328212251.273  848  283964,\
a 104 0001 1002 050328222916.883 050502211342.740  850  281869,\
a 105 0001 1002 050502222924.357 050606212258.752  787  252441,\
a 106 0001 1002 050606222924.395 050711212254.543  786  255472,\
a 107 0001 1002 050711222921.310 050815212253.584  782  278007,\
a 108 0001 1002 050815222925.915 050919212250.819  826  304657,\
a 109 0001 1002 050919222919.497 051024212235.175  793  291370,\
a 110 0001 1002 051024222919.622 051128212241.557  821  282845,\
a 111 0001 1002 051128223724.283 060102211327.695  831  280714,\
a 112 0001 1002 060102222921.367 060206212242.149  836  289869,\
a 113 0001 1002 060206222922.161 060313212242.666  835  277867,\
a 114 0001 1002 060313222924.246 060417212249.542  824  279384,\
a 115 0001 1002 060417222929.230 060522212244.617  825  285563,\
a 116 0001 1002 060522222929.920 060626212250.200  830  275545,\
a 117 0001 1002 060626222931.240 060731212254.413  766  272947,\
a 118 0001 1002 060731222933.769 060904212247.720  786  299171,\
a 119 0001 1002 060904222931.696 061009212241.706  822  274841,\
a 120 0001 1002 061009222925.954 061113212236.025  829  275881,\
a 121 0001 1002 061113222918.853 061218212240.663  829  287820,\
a 122 0001 1002 061218222923.412 070122212241.392  691  232000,\
a 123 0001 1002 070122222923.535 070226212244.245  800  265715,\
a 124 0001 1002 070226222924.769 070402212248.989  827  280587,\
a 125 0001 1002 070402223731.950 070507212241.799  777  260557,\
a 126 0001 1002 070507222932.910 070611212242.199  802  265551,\
a 127 0001 1002 070611222924.625 070716212221.292  766  260714,\
a 128 0001 1002 070716222925.402 070820211323.726  785  285886,\
a 129 0001 1002 070820222920.722 070924212232.401  832  304438,\
a 130 0001 1002 070924222921.569 071029212255.736  822  301147,\
a 131 0001 1002 071029222937.665 071203212307.699  834  290337,\
a 132 0001 1002 071203223752.364 080107212324.776  830  274402,\
a 133 0001 1002 080107222958.573 080211212343.791  815  271374,\
a 134 0001 1002 080211223008.422 080317212351.429  834  277298,\
a 135 0001 1002 080317223025.849 080421212402.853  854  306952,\
a 136 0001 1002 080421223033.816 080526211457.338  917  365762,\
a 137 0001 1002 080526223031.738 080630212409.821  890  365231,\
a 138 0001 1002 080630223045.157 080804212410.018  845  385853,\
a 139 0001 1002 080804223044.647 080908215910.900  881  467334,\
a 140 0001 1002 080908223021.026 081013212357.938  888  429149,\
a 141 0001 1002 081013223039.437 081117212403.193  884  405165,\
a 142 0001 1002 081117223018.494 081222212414.895  888  385244,\
a 143 0001 1002 081222223051.247 090126212433.132  863  342813,\
a 144 0001 1002 090126223056.145 090302212451.582  901  376350,\
a 145 0001 1002 090302223125.117 090406215846.717  909  383550,\
a 146 0001 1002 090406223139.106 090511211610.233  867  313695,\
a 147 0001 1002 090511223132.532 090615211616.987  728  266959,\
a 148 0001 1002 090615223155.157 090720215911.552  864  354762,\
a 149 0001 1002 090720223206.052 090824215857.794  782  319807,\
a 150 0001 1001 090824223213.050 090928211522.397  843  335467,\
a 151 0001 1002 090928223155.379 091102211621.466  799  315244,\
a 152 0001 1002 091102223202.277 091207215905.640  827  305983,\
a 153 0001 1002 091207223144.727 100111211612.147  834  306602,\
a 154 0001 1002 100111224005.390 100215211555.496  756  268237,\
a 155 0001 1002 100215223131.063 100322211546.100  836  308921,\
a 156 0001 1002 100322223124.205 100426211528.087  872  308663,\
a 157 0001 1002 100426223047.831 100531211526.140  851  300321,\
a 158 0001 1002 100531223056.117 100705215812.804  802  274186,\
a 159 0001 1002 100705223056.269 100809211548.959  778  342895,\
a 160 0001 1002 100809223124.994 100913215839.190  880  412231,\
a 161 0001 1002 100913223136.232 101018211615.641  835  335434,\
a 162 0001 0998 101018223140.677 101122181611.750  627  265713,\
a 163 0001 1002 101122223152.824 101227211628.386  550  259668,\
a 164 0001 1002 101227223204.956 110131211625.750  596  248382,\
a 165 0001 0861 110131223156.321 110302233850.052  749  279303"

DURATIONS={'a':35}

from ersCycles import SatPhasesCycles

class Ers2PhasesCycles(SatPhasesCycles): 
        global HEADER,DATA
        #
        #
        #
        def __init__(self, label=None):
            SatPhasesCycles.__init__(self, label, HEADER, DATA)

            for key in DURATIONS.keys():
                print "set duration for phase:'%s'" % key
                phase=self.getPhase(key)
                phase.setDuration(DURATIONS[key])


            
if __name__ == '__main__':
    label="ERS2"
    print "%s cycles" % label
    ers = Ers2PhasesCycles(label)
    print "\n\ndump: %s" % ers.info()







