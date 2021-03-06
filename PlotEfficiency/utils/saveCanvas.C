// macro to save all TCanvas with a name matching (regex) a passed pattern.

#include "general_helpers.h"

#include "TObject.h"
#include "TFile.h"
#include "TDirectory.h"
#include "TCanvas.h"

#include <iostream>
#include <regex>
#include <string>

/**
 * Functor that saves a TCanvas if its name matches the internal regex.
 * The resulting filename is the path to the TCanvas _inside_ the rootfile where all "/" are replaced with ":"
 * and the name of the fit_canvas is appended to that path
 *
 * Example: TCanvas with name "can" is stored in /TDirectory/path/to/TCanvas, then the output .pdf file will be
 * :TDirectory:path:to:TCanvas_can.pdf
 *
 * This is realized as functor due to two reasons:
 * 1) The interface requires to only have a TObject* as single argument
 * 2) The internal value of the current path can be easily changed.
 */
struct saveCanvasIfMatch {
  /**
   * Constructor. The regex is stored as const reference and has thus to be known at initialization.
   * The extension determines in which format the plots will be stored. NOTE: there is no check as to wether TCanvas::SaveAs()
   * can handle the passed extension!
   */
  explicit saveCanvasIfMatch(const std::regex& regex, const std::string& extension = "pdf") :
    m_rgx(regex), m_fileExtension(extension) {;}

  /**
   * operator() provides the required interface.
   * Checks if obj is a TCanvas and if it's name matches the regex. If this is the case a filename is generated
   * from the currently set m_currentPath and the name of the TCanvas and it is saved in the format specified by the fileExtension.
   */
  void operator()(TObject* obj);

  /** set the internal path variable to the path of the passed TDirectory. */
  void setCurrentPath(const TDirectory* dir) { m_currentPath = dir->GetPath(); }

private:
  const std::regex& m_rgx;
  std::string m_currentPath{};
  std::string m_fileExtension{"pdf"};
};

void saveCanvasIfMatch::operator()(TObject* obj)
{
  if (inheritsFrom<TCanvas>(obj)) {
    TCanvas* can = static_cast<TCanvas*>(obj);
    if (std::regex_match(can->GetName(), m_rgx)) {
      // the TDirectory::GetPath() method returns in the fromat /file/on/disk:/path/in/file
      std::string path = splitString(m_currentPath, ':')[1];
      replace(path, "/", ":"); // do not want to make a directory system to save the files
      // This should work with (e.g.) png, but does currently not.
      can->SaveAs((path + "_" + can->GetName() + "." + m_fileExtension).c_str());
    }
  }
}

/**
 * Due to some -Wundefined-internal warnings when compiling with .L in the root interpreter I define this one-liner
 * here that is then used below via std::bind.
 */
inline void updateDir(saveCanvasIfMatch& matcher, TDirectory* dir)
{
  matcher.setCurrentPath(dir);
}

/**
 * root entry point and "main" function.
 * Recurses over all TDirectories found in the file and runs the saveCanvasIfMatch.operator() on every TObject that
 * is not a TDirectory. (See general_helper.h for the definition of the recurseOnFile function for more info)
 */
void saveCanvas(const std::string& filename, const std::string& canvasRgx, const std::string& fileExtension = "pdf")
{
  TFile* file = TFile::Open(filename.c_str(), "READ");
  if (!file) {
    std::cerr << "Cannot open file \'" << filename << "\'" << std::endl;
    exit(1);
  }

  const std::regex rgx(canvasRgx);
  saveCanvasIfMatch canvasMatcher(rgx, fileExtension);
  canvasMatcher.setCurrentPath(file);
  // This mess with invoking std::bind and a one-line function defined above seems unnecessary, but when compiling
  // via .L in the root interpreter, a version with a lambda instead rises a bunch of -Wundefined-internal warnings
  // For some reason gcc works with the lambda without complaining, but cling does not
  recurseOnFile(file, canvasMatcher, std::bind(updateDir, std::ref(canvasMatcher), std::placeholders::_1));
}

#ifndef __CINT__
int main(int argc, char* argv[])
{
  if (argc < 3) {
    std::cerr << "Need a .root file and a canvas name (regex) as input" << std::endl;
  }

  std::string fileExt = "pdf";
  if (argc >= 3) {
    std::string tmpStr = argv[3];
    if (tmpStr != "pdf" && tmpStr != "ps" && tmpStr != "svg") {
      std::cerr << "Cannot use \'" << tmpStr << "\' as a file extension! Using pdf instead!" << std::endl;
      // TODO find out why TCanvas::SaveAs() does not work as advertised with other extensions like png and gif.
      std::cerr << "\'ps\' and \'pdf\' \'svg\'are allowed file extensions" << std::endl;
      tmpStr = "pdf";
    }
    fileExt = tmpStr;
  }

  saveCanvas(argv[1], argv[2], fileExt);

  return 0;
}
#endif
