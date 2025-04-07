%chk=896275.chk
%mem=4GB
%NProcShared=1
#P SP CASSCF(2,2)/6-311G** gfinput fchk=all density=current iop(5/33=1) out=wfx

896275 helium CASSCF(2,2) 6-311G**

0 1
He    0.0000   0.0000   0.0000

896275.wfx

