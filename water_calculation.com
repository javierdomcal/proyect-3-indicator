%chk=water.chk
%mem=2GB
%NProcShared=1
#P SP/HF 6-31G gfinput fchk=all IOP(3/32=2) IOP(8/11=1) IOP(6/97=20) SCF(qc) IOP(6/93=2)  use=l802 out=wfx iop(9/40=7) iop(9/28=-1) use=l916 IOP(3/26=11) IOP(3/27=20) IOP(6/95=8) IOP(6/98=0) IOP(6/99=-1) IOP(6/7=3)

Water Calculation water HF 6-31G

0 1
O    0.0000   0.0000   0.0000
H    0.7572   0.5860   0.0000
H   -0.7572   0.5860   0.0000

water.wfn
