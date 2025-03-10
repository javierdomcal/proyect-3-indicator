%chk=helium_CASSCF(2,2)_6-311G.chk
%mem=4GB
%NProcShared=1
#P SP CASSCF(2,2)/6-311G gfinput fchk=all density=current iop(5/33=1) out=wfx

helium_CASSCF(2,2)_6-311G helium CASSCF(2,2) 6-311G

0 1
He    0.0000   0.0000   0.0000

helium_CASSCF(2,2)_6-311G.wfx
