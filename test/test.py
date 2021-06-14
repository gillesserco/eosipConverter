

import os

DOC_REF_TYPECODE = "SAR_SX_SLC - SAR_SX_SGF - SAR_SX_SGX - SAR_SX_SSG - SAR_SX_SPG - SAR_WX_SLC - SAR_WX_SGF - SAR_WX_SGX - SAR_WX_SSG - SAR_WX_SPG - SAR_FX_SLC - SAR_FX_SGF - SAR_FX_SGX - SAR_FX_SSG - SAR_FX_SPG - SAR_FW_SLC - SAR_FW_SGF - SAR_FW_SGX - SAR_FW_SSG - SAR_FW_SPG - SAR_MF_SLC - SAR_MF_SGF - SAR_MF_SGX - SAR_MF_SSG - SAR_MF_SPG - SAR_MW_SLC - SAR_MW_SGF - SAR_MW_SGX - SAR_MW_SSG - SAR_MW_SPG - SAR_EF_SLC - SAR_EF_SGF - SAR_EF_SGX - SAR_EF_SSG - SAR_EF_SPG - SAR_UF_SLC - SAR_UF_SGF - SAR_UF_SGX - SAR_UF_SSG - SAR_UF_SPG - SAR_UW_SLC - SAR_UW_SGF - SAR_UW_SGX - SAR_UW_SSG - SAR_UW_SPG - SAR_EH_SLC - SAR_EH_SGF - SAR_EH_SGX - SAR_EH_SSG - SAR_EH_SPG - SAR_EL_SLC - SAR_EL_SGF - SAR_EL_SGX - SAR_EL_SSG - SAR_EL_SPG - SAR_SQ_SLC - SAR_SQ_SGX - SAR_SQ_SSG - SAR_SQ_SPG - SAR_QS_SLC - SAR_QS_SGX - SAR_QS_SSG - SAR_QS_SPG - SAR_FQ_SLC - SAR_FQ_SGX - SAR_FQ_SSG - SAR_FQ_SPG - SAR_QF_SLC - SAR_QF_SGX - SAR_QF_SSG - SAR_QF_SPG - SAR_SN_SCN - SAR_SN_SCF - SAR_SN_SCS - SAR_SW_SCW - SAR_SW_SCF - SAR_SW_SCS - SAR_SL_SLC - SAR_SL_SGF - SAR_SL_SGX - SAR_SL_SSG - SAR_SL_SPG"
SOFT_REF_TYPECODES=['SAR_SX_SLC', 'SAR_SX_SGF', 'SAR_SX_SGX', 'SAR_SX_SSG', 'SAR_SX_SPG', 'SAR_WX_SLC', 'SAR_WX_SGF', 'SAR_WX_SGX', 'SAR_WX_SSG', 'SAR_WX_SPG', 'SAR_FX_SLC', 'SAR_FX_SGF', 'SAR_FX_SGX', 'SAR_FX_SSG', 'SAR_FX_SPG', 'SAR_FW_SLC', 'SAR_FW_SGF', 'SAR_FW_SGX', 'SAR_FW_SSG', 'SAR_FW_SPG', 'SAR_MF_SLC', 'SAR_MF_SGF', 'SAR_MF_SGX', 'SAR_MF_SSG', 'SAR_MF_SPG', 'SAR_MW_SLC', 'SAR_MW_SGF', 'SAR_MW_SGX', 'SAR_MW_SSG', 'SAR_MW_SPG', 'SAR_EF_SLC', 'SAR_EF_SGF', 'SAR_EF_SGX', 'SAR_EF_SSG', 'SAR_EF_SPG', 'SAR_UF_SLC', 'SAR_UF_SGF', 'SAR_UF_SGX', 'SAR_UF_SSG', 'SAR_UF_SPG', 'SAR_UW_SLC', 'SAR_UW_SGF', 'SAR_UW_SGX', 'SAR_UW_SSG', 'SAR_UW_SPG', 'SAR_EH_SLC', 'SAR_EH_SGF', 'SAR_EH_SGX', 'SAR_EH_SSG', 'SAR_EH_SPG', 'SAR_EL_SLC', 'SAR_EL_SGF', 'SAR_EL_SGX', 'SAR_EL_SSG', 'SAR_EL_SPG', 'SAR_SQ_SLC', 'SAR_SQ_SGX', 'SAR_SQ_SSG', 'SAR_SQ_SPG', 'SAR_QS_SLC', 'SAR_QS_SGX', 'SAR_QS_SSG', 'SAR_QS_SPG', 'SAR_FQ_SLC', 'SAR_FQ_SGX', 'SAR_FQ_SSG', 'SAR_FQ_SPG', 'SAR_QF_SLC', 'SAR_QF_SGX', 'SAR_QF_SSG', 'SAR_QF_SPG', 'SAR_SN_SCN', 'SAR_SN_SCF', 'SAR_SN_SCS', 'SAR_SW_SCW', 'SAR_SW_SCF', 'SAR_SW_SCS', 'SAR_SL_SLC', 'SAR_SL_SGF', 'SAR_SL_SGX', 'SAR_SL_SSG', 'SAR_SL_SPG']
SOFT_REF_TYPECODES.sort()

DOC_BOUNDING_BOX_TYPECODES = "SAR_SX_SSG - SAR_SX_SPG - SAR_WX_SSG - SAR_WX_SPG - SAR_FX_SSG - SAR_FX_SPG - SAR_FW_SSG - SAR_FW_SPG - SAR_MF_SSG - SAR_MF_SPG - SAR_MW_SSG - SAR_MW_SPG - SAR_EF_SSG - SAR_EF_SPG - SAR_UF_SSG - SAR_UF_SPG - SAR_UW_SSG - SAR_UW_SPG - SAR_EH_SSG - SAR_EH_SPG - SAR_EL_SSG - SAR_EL_SPG - SAR_SQ_SSG - SAR_SQ_SPG - SAR_QS_SSG - SAR_QS_SPG - SAR_FQ_SSG - SAR_FQ_SPG - SAR_QF_SSG - SAR_QF_SPG - SAR_SL_SSG - SAR_SL_SPG"
SOFT_BOUNDING_BOX_TYPECODES=['SAR_SX_SSG', 'SAR_SX_SPG', 'SAR_WX_SSG', 'SAR_WX_SPG', 'SAR_FX_SSG', 'SAR_FX_SPG', 'SAR_FW_SSG', 'SAR_FW_SPG', 'SAR_MF_SSG', 'SAR_MF_SPG', 'SAR_MW_SSG', 'SAR_MW_SPG', 'SAR_EF_SSG', 'SAR_EF_SPG', 'SAR_UF_SSG', 'SAR_UF_SPG', 'SAR_UW_SSG', 'SAR_UW_SPG', 'SAR_EH_SSG', 'SAR_EH_SPG', 'SAR_EL_SSG', 'SAR_EL_SPG', 'SAR_SQ_SSG', 'SAR_SQ_SPG', 'SAR_QS_SSG', 'SAR_QS_SPG', 'SAR_FQ_SSG', 'SAR_FQ_SPG', 'SAR_QF_SSG', 'SAR_QF_SPG', 'SAR_SL_SSG', 'SAR_SL_SPG']
SOFT_BOUNDING_BOX_TYPECODES.sort()


DOC_REF_TYPECODE_SORTED = []
for item in DOC_REF_TYPECODE.split(" - "):
    DOC_REF_TYPECODE_SORTED.append(item)
DOC_REF_TYPECODE_SORTED.sort()

DOC_BOUNDING_BOX_TYPECODES_SORTED = []
for item in DOC_BOUNDING_BOX_TYPECODES.split(" - "):
    DOC_BOUNDING_BOX_TYPECODES_SORTED.append(item)
DOC_BOUNDING_BOX_TYPECODES_SORTED.sort()

print ("num SOFT_REF_TYPECODES:%s" % len(SOFT_REF_TYPECODES))
print ("num DOC_REF_TYPECODE_SORTED:%s" % len(DOC_REF_TYPECODE_SORTED))
print ("SOFT_REF_TYPECODES     :%s" % SOFT_REF_TYPECODES)
print ("DOC_REF_TYPECODE_SORTED:%s" % DOC_REF_TYPECODE_SORTED)

print ("\n\n\n\nnum DOC_BOUNDING_BOX_TYPECODES_SORTED:%s" % len(DOC_BOUNDING_BOX_TYPECODES_SORTED))
print ("num SOFT_BOUNDING_BOX_TYPECODES:%s" % len(SOFT_BOUNDING_BOX_TYPECODES))

print ("DOC_BOUNDING_BOX_TYPECODES_SORTED    :%s" % DOC_BOUNDING_BOX_TYPECODES_SORTED)
print ("SOFT_BOUNDING_BOX_TYPECODES          :%s" % SOFT_BOUNDING_BOX_TYPECODES)

os._exit(0)
missing=[]
if len(DOC_BOUNDING_BOX_TYPECODES_SORTED) != len(SOFT_BOUNDING_BOX_TYPECODES):
    n=0
    for item in DOC_BOUNDING_BOX_TYPECODES_SORTED:
        print("  test %s:%s" % (n,item))
        if item not in SOFT_BOUNDING_BOX_TYPECODES:
            print(" missing %s in SOFT_BOUNDING_BOX_TYPECODES:%s" % (n, item))
            missing.append(item)
        else:
            print(" item %s in SOFT_BOUNDING_BOX_TYPECODES:%s" % (n, item))
        n+=1

    print ("missing in SOFT_BOUNDING_BOX_TYPECODES:%s" % missing)

    print(set(DOC_BOUNDING_BOX_TYPECODES_SORTED) - set(SOFT_BOUNDING_BOX_TYPECODES))


os._exit(0)