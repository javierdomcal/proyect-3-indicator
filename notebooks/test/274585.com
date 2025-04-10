%chk=274585.chk
%mem=4GB
%NProcShared=1
#P SP CASSCF(2,2)/cc-pVDZ gfinput fchk=all density=current iop(5/33=1) out=wfx

274585 helium CASSCF(2,2) cc-pVDZ

0 1
He    0.0000   0.0000   0.0000

274585.wfx

