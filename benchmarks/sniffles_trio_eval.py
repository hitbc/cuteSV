import sys
import argparse
import logging
import time

def load_parent_info(path):
	homo_P = dict()
	total_P = dict()
	linkage = 0
	Tag = dict()
	file = open(path, 'r')
	for line in file:
		seq = line.strip('\n').split('\t')
		if seq[0][0] == "#":
			continue

		chr_1 = seq[0]
		pos_1 = int(seq[1])
		svtype = seq[4]
		info = seq[7]
		chr_2 = info.split(";")[2].split("=")[1]
		pos_2 = int(info.split(";")[3].split("=")[1])
		svlen = int(info.split(";")[11].split("=")[1])
		GT = seq[9].split(':')[0]

		if svtype not in Tag:
			Tag[svtype] = 0
		Tag[svtype] += 1

		if svtype not in total_P:
			total_P[svtype] = dict()
		if chr_1 not in total_P[svtype]:
			total_P[svtype][chr_1] = dict()
		hash_1 = int(pos_1/10000)
		mod = pos_1 % 10000
		hash_2 = int(mod/50)
		if hash_1 not in total_P[svtype][chr_1]:
			total_P[svtype][chr_1][hash_1] = dict()
		if hash_2 not in total_P[svtype][chr_1][hash_1]:
			total_P[svtype][chr_1][hash_1][hash_2] = list()

		if GT == '1/1':
			linkage += 1
			homo_P[linkage] = [chr_1, pos_1, chr_2, pos_2, svlen, svtype]
			total_P[svtype][chr_1][hash_1][hash_2].append([pos_1, chr_2, pos_2, svlen, 'Y', linkage])
		else:
			total_P[svtype][chr_1][hash_1][hash_2].append([pos_1, chr_2, pos_2, svlen, 'N', 0])
		# print chr_1, pos_1, chr_2, pos_2, svlen, svtype, GT
	file.close()
	return homo_P, total_P, Tag

def acquire_locus(down, up, keytype, chr, MainCandidate):
	back_ele = list()
	if keytype not in MainCandidate:
		return []
	if chr not in MainCandidate[keytype]:
		return []
	if int(up/10000) == int(down/10000):
		key_1 = int(down/10000)
		if key_1 not in MainCandidate[keytype][chr]:
			return []
		for i in xrange(int((up%10000)/50)-int((down%10000)/50)+1):
			# exist a bug ***********************************
			key_2 = int((down%10000)/50)+i
			if key_2 not in MainCandidate[keytype][chr][key_1]:
				continue
			for ele in MainCandidate[keytype][chr][key_1][key_2]:
				if ele[0] >= down and ele[0] <= up:
					# return ele
					back_ele.append(ele)
			return back_ele
	else:
		key_1 = int(down/10000)
		if key_1 in MainCandidate[keytype][chr]:
			for i in xrange(200-int((down%10000)/50)):
				# exist a bug ***********************************
				key_2 = int((down%10000)/50)+i
				if key_2 not in MainCandidate[keytype][chr][key_1]:
					continue
				for ele in MainCandidate[keytype][chr][key_1][key_2]:
					if ele[0] >= down and ele[0] <= up:
						back_ele.append(ele)
				return back_ele
		key_1 += 1
		if key_1 not in MainCandidate[keytype][chr]:
			return []
		for i in xrange(int((up%10000)/50)+1):
			# exist a bug ***********************************
			key_2 = i
			if key_2 not in MainCandidate[keytype][chr][key_1]:
				continue
			for ele in MainCandidate[keytype][chr][key_1][key_2]:
				if ele[0] >= down and ele[0] <= up:
					back_ele.append(ele)
			return back_ele
	return []

def main_ctrl(args):
	logging.info("Loading Male parent callsets.")
	homo_MP, total_MP, Tag = load_parent_info(args.MP)
	# print len(homo_MP)
	logging.info("Homozygous SV is %d in %s."%(len(homo_MP), args.MP))
	for key in Tag:
		logging.info("Type %s SV is %d."%(key, Tag[key]))

	logging.info("Loading Female parent callsets.")
	homo_FP, total_FP, Tag = load_parent_info(args.FP)
	# print len(homo_FP)
	logging.info("Homozygous SV is %d in %s."%(len(homo_FP), args.FP))
	for key in Tag:
		logging.info("Type %s SV is %d."%(key, Tag[key]))

	logging.info("Loading Offspring callsets.")
	recall = 0
	total_call = 0
	tag = dict()
	file = open(args.F1, 'r')
	for line in file:
		seq = line.strip('\n').split('\t')
		if seq[0][0] == "#":
			continue

		total_call += 1
		flag = 0
		chr_1 = seq[0]
		pos_1 = int(seq[1])
		svtype = seq[4]
		if svtype not in tag:
			tag[svtype] = 0
		tag[svtype] += 1
		info = seq[7]
		chr_2 = info.split(";")[2].split("=")[1]
		pos_2 = int(info.split(";")[3].split("=")[1])
		svlen = int(info.split(";")[11].split("=")[1])
		# GT = seq[9].split(':')[0]
		# if pos_1 == 1287701:
		# 	print chr_1, pos_1, chr_2, pos_2, svlen, svtype
		# 	print total_MP[svtype][chr_1][128]
		# 	print acquire_locus(pos_1-50, pos_1+50, svtype, chr_1, total_MP) 
		ans_MP = acquire_locus(pos_1-50, pos_1+50, svtype, chr_1, total_MP)
		if len(ans_MP) > 0:
			flag = 1
			for ele in ans_MP:
				if ele[4] == 'Y':
					homo_MP[ele[5]] = 1
		ans_FP = acquire_locus(pos_1-50, pos_1+50, svtype, chr_1, total_FP)
		if len(ans_FP) > 0:
			flag = 1
			for ele in ans_FP:
				if ele[4] == 'Y':
					homo_FP[ele[5]] = 1
		if flag == 1:
			recall += 1

	file.close()
	for key in tag:
		logging.info("Type %s SV is %d."%(key, tag[key]))
	logging.info("Accuracy rate %d/%d"%(recall, total_call))
	total_right = 0
	for key in homo_MP:
		if homo_MP[key] == 1:
			total_right += 1
		# else:
		# 	print homo_MP[key]
	for key in homo_FP:
		if homo_FP[key] == 1:
			total_right += 1
		# else:
		# 	print homo_FP[key]
	logging.info("Sensitivity rate %d/%d"%(total_right, len(homo_FP)+len(homo_MP)))

def main(argv):
	args = parseArgs(argv)
	setupLogging(False)
	# print args
	starttime = time.time()
	main_ctrl(args)
	logging.info("Finished in %0.2f seconds."%(time.time() - starttime))

USAGE="""\
	Evaluate SV callset generated by Sniffles
"""

def parseArgs(argv):
	parser = argparse.ArgumentParser(prog="Trio_eval", description=USAGE, formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.add_argument("MP", type=str, help="Male parent callsets")
	parser.add_argument('FP', type=str, help = "Female parent callsets")
	parser.add_argument('F1', type=str, help = "Offspring callsets")
	# parser.add_argument('-s', '--min_support', help = "Minimum number of reads that support a SV to be reported.[%(default)s]", default = 10, type = int)
	args = parser.parse_args(argv)
	return args

def setupLogging(debug=False):
	logLevel = logging.DEBUG if debug else logging.INFO
	logFormat = "%(asctime)s [%(levelname)s] %(message)s"
	logging.basicConfig( stream=sys.stderr, level=logLevel, format=logFormat )
	logging.info("Running %s" % " ".join(sys.argv))

if __name__ == '__main__':
	main(sys.argv[1:])