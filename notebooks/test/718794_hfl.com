%chk=718794_hfl.chk
%mem=4GB
%NProcShared=1
#P SP CASSCF(2,2)/6-311G** gfinput fchk=all density=current iop(5/33=1) out=wfx

718794 helium CASSCF(2,2) 6-311G**

0 1
He    0.0000   0.0000   0.0000

718794_hfl.wfx

